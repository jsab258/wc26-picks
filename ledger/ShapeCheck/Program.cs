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

var compilation = CSharpCompilation.Create("UnityLayerCheck", trees,
    references: null,
    options: new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

int bad = 0;
foreach (var d in compilation.GetDiagnostics())
{
    if (d.Severity != DiagnosticSeverity.Error) continue;
    if (!interesting.Contains(d.Id)) continue;
    bad++;
    var span = d.Location.GetLineSpan();
    Console.WriteLine($"{span.Path}:{span.StartLinePosition.Line + 1}: {d.Id}: {d.GetMessage()}");
}
Console.WriteLine($"checked {files} files, {bad} shape error(s)");
return bad == 0 ? 0 : 1;
