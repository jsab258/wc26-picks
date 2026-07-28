using System.Linq;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;

// Semantic-ish check over the Unity layer, which nothing else in this project
// compiles: CoreTests compiles Core only, and Unity itself is twenty minutes
// away on a CI runner.
//
// The trick is to build a real CSharpCompilation with NO references and then
// keep only the diagnostics that do not depend on having any. Missing types
// (CS0246, CS0234, CS0103...) are expected and discarded; what survives are the
// errors that are purely about the code's own shape — duplicate locals,
// duplicate members, unreachable returns, use before assignment. That is
// exactly the family that has been costing twenty-minute round trips.
var interesting = new HashSet<string>
{
    "CS0128", // duplicate local
    "CS0136", // local conflicts with enclosing scope
    "CS0102", // duplicate member
    "CS0111", // duplicate method signature
    "CS0100", // duplicate parameter
    "CS0106", // modifier not valid here
    // CS0161/CS0177/CS0843 are flow analysis and DO depend on references —
    // without System.Threading.Tasks an async method looks like it never
    // returns. Excluded: they fire on four healthy methods here.
    "CS0501", // must declare a body
    "CS0759", // partial method without implementation
    "CS8112", // local function never used / must have body
    "CS1002", "CS1513", "CS1519", "CS1022", // syntax, kept for completeness
};

var trees = new List<SyntaxTree>();
int files = 0;
foreach (var path in Directory.EnumerateFiles(args[0], "*.cs", SearchOption.AllDirectories))
{
    if (path.Contains("/obj/") || path.Contains("/bin/")) continue;
    files++;
    trees.Add(CSharpSyntaxTree.ParseText(File.ReadAllText(path),
        new CSharpParseOptions(LanguageVersion.CSharp9), path: path));
}

// Every type name WE declare, so a CS0246 naming one of them (or a common
// BCL container) is a missing using rather than Unity noise.
var ourTypes = new HashSet<string>();
foreach (var t in trees)
    foreach (var node in t.GetRoot().DescendantNodes())
        switch (node)
        {
            case Microsoft.CodeAnalysis.CSharp.Syntax.BaseTypeDeclarationSyntax btd:
                ourTypes.Add(btd.Identifier.Text); break;
            case Microsoft.CodeAnalysis.CSharp.Syntax.DelegateDeclarationSyntax dd:
                ourTypes.Add(dd.Identifier.Text); break;
        }

var compilation = CSharpCompilation.Create("UnityLayerCheck", trees,
    references: null,
    options: new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

// CS0103 ("the name X does not exist") is the diagnostic this checker was
// built to catch and the one it has been throwing away, because without
// references every unknown TYPE raises it too — GameObject, Vector3, Mathf,
// all of them. Discarding the whole id meant a mistyped LOCAL sailed through
// and cost a nine-minute round trip on the runner, twice.
//
// The split is cheap and holds across this codebase: unresolved types are
// PascalCase and unresolved locals are camelCase. So keep CS0103 only when
// the missing name begins with a lower-case letter. On a clean tree that
// reports nothing; on the run that motivated it, it reports exactly the one
// line that broke the build.
//
// It is a heuristic and it is allowed to be: the cost of a false positive is
// renaming a local, and the cost of the false negative it replaces is a
// twenty-minute build that fails on a typo.
// The exceptions are the lower-case members a MonoBehaviour INHERITS, which
// are camelCase and unresolvable for the same reason every Unity type is.
// Small, closed, and the compiler will tell us loudly if the list ever needs
// another entry — a new one shows up as a false positive here, not as a
// silent miss on the runner.
var inherited = new HashSet<string>
{
    "transform", "gameObject", "enabled", "tag", "name", "hideFlags",
    "isActiveAndEnabled", "useGUILayout", "runInEditMode",
    // "rigidbody" and "camera" were here — Unity 5 removed those shortcut
    // properties, so whitelisting them turned a genuine CS0103 into a silent
    // miss, the exact thing the comment above promises cannot happen (audit
    // 2026-07-27).
};

static bool MissingTypeName(Diagnostic d, out string name)
{
    name = null;
    var msg = d.GetMessage();
    int open = msg.IndexOf('\'');
    int close = open >= 0 ? msg.IndexOf('\'', open + 1) : -1;
    if (open < 0 || close <= open + 1) return false;
    name = msg.Substring(open + 1, close - open - 1);
    int generic = name.IndexOf('<');
    if (generic > 0) name = name.Substring(0, generic);   // List<> -> List
    return name.Length > 0;
}

static bool MissingName(Diagnostic d, out string name)
{
    name = null;
    if (d.Id != "CS0103") return false;
    var msg = d.GetMessage();
    int open = msg.IndexOf('\'');
    int close = open >= 0 ? msg.IndexOf('\'', open + 1) : -1;
    if (open < 0 || close <= open + 1) return false;
    name = msg.Substring(open + 1, close - open - 1);
    return true;
}

int bad = 0;
foreach (var d in compilation.GetDiagnostics())
{
    if (d.Severity != DiagnosticSeverity.Error) continue;
    // Leading underscores count as lower-case for this purpose. Private
    // fields in this codebase are all _likeThis, and the first version of this
    // check tested char.IsLower(name[0]) — which is false for '_', so the most
    // common typo in the codebase was the one class it silently skipped. A
    // checker with a hole exactly where the code is densest is worse than no
    // checker, because it is trusted.
    // The inherited-member exemption is for MonoBehaviours; Core is
    // engine-free, so a bare "name" or "enabled" typo there is a REAL
    // CS0103 the whitelist used to swallow (audit 2026-07-27).
    var file = (d.Location.SourceTree?.FilePath ?? "").Replace('\\', '/');
    bool engineFile = !file.Contains("/Core/");
    bool missingLocal = MissingName(d, out var missing)
                        && char.IsLower(missing.TrimStart('_').FirstOrDefault())
                        && !(engineFile && inherited.Contains(missing));
    // CS0246 for a type WE declared, or for a common BCL type, means a
    // missing using — a real break the old filter discarded with the
    // Unity noise. Two CI builds died on exactly this before the sim ever
    // ran (List<> in SaveSlots, OperationPlan in UiSmokeTest, 2026-07-28):
    // the compiler upstairs caught what this file was built to catch.
    // Only types WE declared: this compilation has no reference assemblies
    // at all, so every BCL name is CS0246 by construction and only
    // cross-tree resolution of our own namespaces is meaningful. (The BCL
    // half of this class of break lives in lint-usings.py, textually.)
    bool missingOurType = d.Id == "CS0246" && MissingTypeName(d, out var typeName)
                          && ourTypes.Contains(typeName);
    if (!interesting.Contains(d.Id) && !missingLocal && !missingOurType) continue;
    bad++;
    var span = d.Location.GetLineSpan();
    Console.WriteLine($"{span.Path}:{span.StartLinePosition.Line + 1}: {d.Id}: {d.GetMessage()}");
}
Console.WriteLine($"checked {files} files, {bad} shape error(s)");
return bad == 0 ? 0 : 1;
