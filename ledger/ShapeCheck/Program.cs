using System.Collections.Generic;
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
    // Real semantics, available only since the BCL references were added.
    // Every one of these is a question about a type Roslyn can actually see;
    // anything involving a Unity type has an error-typed receiver and is
    // suppressed by the compiler before it reaches here.
    "CS1061", // no such member on a known type  <- the List<object> bug
    "CS1503", // argument type mismatch          <- its two follow-on errors
    "CS0029", // cannot implicitly convert
    "CS1929", // extension method needs a different receiver type
    // CS0019 (operator not applicable) was tried and removed the same
    // minute: in this codebase it is almost always about Unity's own maths
    // types — `Vector3? == null` is perfectly legal C# and reads as an error
    // only because Vector3 does not resolve. It bought nothing and cost two
    // false positives, which is how a checker gets ignored.
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

// THE BCL, and nothing else. Added 2026-07-28 after a second Unity-only
// compile error in one night that no local check could see: iterating a
// List<object> as if it were a dictionary. `object.TryGetValue` is a
// question purely about BCL types, and with no references at all Roslyn
// cannot even ask it.
//
// The reason this does not drown the output in Unity noise: Roslyn does not
// report cascading member errors on an ERROR-TYPED receiver. `transform` is
// unresolvable, so `transform.position` produces one CS0103 (already
// discarded) and no CS1061 — while `someObject.TryGetValue` has a receiver
// whose type IS known, and reports. The references buy exactly the
// diagnostics that involve no Unity type and nothing else.
var bcl = new List<MetadataReference>();
foreach (var name in new[]
         {
             "System.Private.CoreLib", "System.Runtime", "System.Collections",
             "System.Linq", "System.Console", "System.Text.RegularExpressions",
         })
{
    try
    {
        var asm = System.Reflection.Assembly.Load(name);
        if (!string.IsNullOrEmpty(asm.Location)) bcl.Add(MetadataReference.CreateFromFile(asm.Location));
    }
    catch (Exception) { /* a missing BCL facade costs coverage, never the run */ }
}

// The ids that exist only because of the references above, so the filter
// below applies to them and to nothing that was already being checked.
var semantic = new HashSet<string> { "CS1061", "CS1503", "CS0029", "CS1929" };

var compilation = CSharpCompilation.Create("UnityLayerCheck", trees,
    references: bcl,
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

// THE ONE FALSE-POSITIVE CLASS the BCL references introduce, and it is
// clean enough to filter exactly.
//
// Our own MonoBehaviours resolve as types (we declare them) but their BASE
// does not, so every inherited member — `transform`, `gameObject`,
// `StartCoroutine` — reads as missing. The receiver type named in the
// message is therefore one of OUR types, and dropping those keeps precisely
// the diagnostics that motivated the references: `'object' does not contain
// a definition for 'TryGetValue'` names a BCL type and survives.
//
// Anything with an error type in it ("?") is also dropped: it means a Unity
// type leaked into the expression and the diagnostic is noise about that
// rather than about our code.
static bool AboutOurOwnUnresolvedBase(Diagnostic d, HashSet<string> ourTypes)
{
    var msg = d.GetMessage();
    if (msg.Contains("'?'") || msg.Contains("(?") || msg.Contains(", ?") || msg.Contains("?,")) return true;
    // Any Unity type ANYWHERE in the message: Roslyn cannot resolve it, so
    // whatever it concluded about the conversion is not a judgement we can
    // trust. A method group converting to a UnityAction is the common case
    // and it compiles perfectly well upstairs.
    if (msg.Contains("UnityEngine.") || msg.Contains("TMPro.")) return true;
    foreach (var t in ourTypes)
        if (msg.Contains("'" + t + "'")) return true;
    return false;
}

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
    // The semantic ids only became askable when the BCL references landed,
    // and they are the only ones that can be about a type whose base we
    // cannot see. Filtered here rather than removed from `interesting`, so
    // the syntax half of the list keeps its old, unconditional behaviour.
    if (semantic.Contains(d.Id) && AboutOurOwnUnresolvedBase(d, ourTypes)) continue;
    bad++;
    var span = d.Location.GetLineSpan();
    Console.WriteLine($"{span.Path}:{span.StartLinePosition.Line + 1}: {d.Id}: {d.GetMessage()}");
}
Console.WriteLine($"checked {files} files, {bad} shape error(s)");
return bad == 0 ? 0 : 1;
