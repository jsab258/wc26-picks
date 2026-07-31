using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

// LAYER 1 — REACH. Does the code run at all?
//
// WHY THIS EXISTS. A gap analysis over 61 public Core APIs in Observation,
// Combat, Homicide, Arsenal, Traces, Reaction and Coat found two untested and
// roughly forty with no call site anywhere in the game. `Brandish` 0.
// `MayFrisk` 0. `Acquire` 0. `Misattribute` 0 — so the street could only ever
// be right about who did it. Three phases of M16 were built, tested, and
// disconnected, and every one of them looked finished in a code review and in
// the test count.
//
// That analysis was done by hand, in an afternoon, once. This is it automated,
// and it runs in about a second.
//
// WHAT IT CAN AND CANNOT KNOW, stated up front because the instrument being
// wrong is this project's third-most expensive habit. There is no semantic
// model here: Unity is not on this machine, so `Assets/Scripts/Game` cannot be
// bound and a receiver's type is unknowable. Matching is therefore by NAME,
// which over-approximates reach — if Core declares `Cost` and the Game calls
// `somethingElse.Cost`, this counts it. Over-approximation means the tool can
// MISS a gap; it will not invent one. So the report grades each hit:
//
//   strong  a call site that names the declaring type: `Traces.Acquire(...)`,
//           `new Coat(...)`, `Arsenal.Table` — unambiguous.
//   weak    the bare member name only, on a receiver whose type is unknown.
//   none    the name does not occur in the Game layer at all. This one is a
//           fact, not an inference, and it is the finding that matters.
//
// The gate fails on `none`. `weak` is printed and counted, never gated on,
// because gating on an inference is how a checker starts flapping and then
// gets switched off.
//
//     dotnet run -c Release --project ledger/ReachCheck -- \
//         ledger/Assets/Scripts/Core ledger/Assets/Scripts/Game \
//         [--allow ledger/ReachCheck/allow.json] [--series] [--json out.json]

string coreDir = args.Length > 0 ? args[0] : "Assets/Scripts/Core";
string gameDir = args.Length > 1 ? args[1] : "Assets/Scripts/Game";
string? allowPath = null, jsonOut = null;
var testDirs = new List<string>();
bool series = false, quiet = false;
for (int i = 2; i < args.Length; i++)
{
    if (args[i] == "--allow" && i + 1 < args.Length) allowPath = args[++i];
    else if (args[i] == "--json" && i + 1 < args.Length) jsonOut = args[++i];
    else if (args[i] == "--tests" && i + 1 < args.Length) testDirs.Add(args[++i]);
    else if (args[i] == "--series") series = true;
    else if (args[i] == "--quiet") quiet = true;
}

static List<SyntaxTree> Parse(string dir)
{
    var trees = new List<SyntaxTree>();
    foreach (var path in Directory.EnumerateFiles(dir, "*.cs", SearchOption.AllDirectories))
    {
        if (path.Contains("/obj/") || path.Contains("/bin/")) continue;
        trees.Add(CSharpSyntaxTree.ParseText(File.ReadAllText(path),
            new CSharpParseOptions(LanguageVersion.CSharp9), path: path));
    }
    return trees;
}

// ---------------------------------------------------------------- the surface

// Members that exist because C# or an interface demands them, not because
// anybody designed them. Gating on these would be gating on boilerplate.
var boring = new HashSet<string>
{
    "ToString", "Equals", "GetHashCode", "GetEnumerator", "Dispose",
    "CompareTo", "Clone", "Deconstruct",
};

// A public API and where it lives.
var api = new List<(string Kind, string Type, string Name, string File, int Line)>();

static bool IsPublic(SyntaxTokenList mods) =>
    mods.Any(m => m.IsKind(SyntaxKind.PublicKeyword));

// A nested type's owner is the outer type, and a call site says `Outer.Inner`
// or just `Inner` — both are handled by keeping the innermost name.
static string OwnerName(SyntaxNode n)
{
    for (var p = n.Parent; p != null; p = p.Parent)
        if (p is BaseTypeDeclarationSyntax b) return b.Identifier.Text;
    return "";
}

var coreTrees = Parse(coreDir);
var coreTypes = new HashSet<string>();

foreach (var tree in coreTrees)
{
    string file = Path.GetFileName(tree.FilePath);
    foreach (var node in tree.GetRoot().DescendantNodes())
    {
        int line = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
        switch (node)
        {
            case TypeDeclarationSyntax t when IsPublic(t.Modifiers):
                coreTypes.Add(t.Identifier.Text);
                api.Add(("type", OwnerName(t), t.Identifier.Text, file, line));
                break;
            case EnumDeclarationSyntax e when IsPublic(e.Modifiers):
                coreTypes.Add(e.Identifier.Text);
                api.Add(("type", OwnerName(e), e.Identifier.Text, file, line));
                break;
            case MethodDeclarationSyntax m when IsPublic(m.Modifiers)
                                                && !boring.Contains(m.Identifier.Text):
                api.Add(("method", OwnerName(m), m.Identifier.Text, file, line));
                break;
            case PropertyDeclarationSyntax p when IsPublic(p.Modifiers):
                api.Add(("property", OwnerName(p), p.Identifier.Text, file, line));
                break;
            case FieldDeclarationSyntax f when IsPublic(f.Modifiers):
                foreach (var v in f.Declaration.Variables)
                    api.Add(("field", OwnerName(f), v.Identifier.Text, file, line));
                break;
        }
    }
}

// Interfaces declare a member that a class then also declares. One entry.
api = api.GroupBy(a => (a.Kind, a.Type, a.Name)).Select(g => g.First()).ToList();

// -------------------------------------------------------------- the call sites

// Every bare name the Game layer mentions, and every `Something.Name` pair.
var mentioned = new HashSet<string>();
var qualified = new HashSet<(string Owner, string Name)>();
// A name the Game layer DECLARES itself is a name this tool cannot attribute:
// `Cost` on a MonoBehaviour and `Cost` in Core look identical from here.
var gameDeclares = new HashSet<string>();

foreach (var tree in Parse(gameDir))
{
    foreach (var node in tree.GetRoot().DescendantNodes())
    {
        switch (node)
        {
            case MemberAccessExpressionSyntax ma:
                mentioned.Add(ma.Name.Identifier.Text);
                if (ma.Expression is IdentifierNameSyntax id)
                    qualified.Add((id.Identifier.Text, ma.Name.Identifier.Text));
                // `Ledger.Core.Traces.Acquire` — the owner is the last hop.
                else if (ma.Expression is MemberAccessExpressionSyntax inner)
                    qualified.Add((inner.Name.Identifier.Text, ma.Name.Identifier.Text));
                break;
            case IdentifierNameSyntax idn:
                mentioned.Add(idn.Identifier.Text);
                break;
            case GenericNameSyntax gn:
                mentioned.Add(gn.Identifier.Text);
                break;
            case ObjectCreationExpressionSyntax oc:
                foreach (var t in oc.Type.DescendantNodesAndSelf().OfType<SimpleNameSyntax>())
                    mentioned.Add(t.Identifier.Text);
                break;
            // `new() { Field = ... }` and `new Foo { Field = ... }` name the
            // member without any receiver at all, which the identifier case
            // above already catches — but an object initialiser's left side is
            // parsed as an assignment, so it is worth being explicit.
            case AssignmentExpressionSyntax asg when asg.Left is IdentifierNameSyntax lid:
                mentioned.Add(lid.Identifier.Text);
                break;
            case BaseTypeDeclarationSyntax btd:
                gameDeclares.Add(btd.Identifier.Text);
                break;
            case MethodDeclarationSyntax gm:
                gameDeclares.Add(gm.Identifier.Text);
                break;
            case PropertyDeclarationSyntax gp:
                gameDeclares.Add(gp.Identifier.Text);
                break;
            case FieldDeclarationSyntax gf:
                foreach (var v in gf.Declaration.Variables) gameDeclares.Add(v.Identifier.Text);
                break;
        }
    }
}

// ------------------------------------------- who else names it: Core, tests
//
// THE FIRST RUN OF THIS TOOL SAID 686 UNREACHED OUT OF 2003, and that number is
// the tool being wrong rather than the codebase being broken. `Vehicle.Braking`
// is state `TrafficSim` owns and steps; the Game has no business naming it, and
// an allowlist with 686 rows in it is a mute button with extra steps.
//
// The incident was never "a public member the Game does not name". It was
// `Brandish`, `MayFrisk`, `Acquire`, `Misattribute`: written, unit-tested,
// green, and wired to nothing. That has a signature this tool can actually see
// — a member the TESTS call and the game does not — and that signature is what
// the gate is built on. Measured first (see `--series`), then gated.
static (HashSet<string> Names, HashSet<string> Files) NamesIn(IEnumerable<string> dirs)
{
    var names = new HashSet<string>();
    var files = new HashSet<string>();
    foreach (var dir in dirs)
    {
        if (!Directory.Exists(dir)) continue;
        foreach (var tree in Parse(dir))
            foreach (var node in tree.GetRoot().DescendantNodes())
                switch (node)
                {
                    case MemberAccessExpressionSyntax ma:
                        names.Add(ma.Name.Identifier.Text);
                        files.Add(ma.Name.Identifier.Text + " " + Path.GetFileName(tree.FilePath));
                        break;
                    case SimpleNameSyntax sn:
                        names.Add(sn.Identifier.Text);
                        files.Add(sn.Identifier.Text + " " + Path.GetFileName(tree.FilePath));
                        break;
                }
    }
    return (names, files);
}

var (testNames, _) = NamesIn(testDirs);

// TRANSITIVE REACHABILITY, because the first attempt at this used "is it named
// in a different Core file" as a proxy and got `IntentRouter.RouteLexical`
// wrong. Nothing outside `IntentRouter.cs` names it — and it runs on every
// line the player types, because `Route` calls it and the Game calls `Route`.
// A same-file caller is not evidence of deadness; it is evidence of a helper.
//
// So: build the call graph inside Core, seed it with every member the Game
// names, and propagate. Edges are by NAME, which over-approximates liveness —
// a member reachable only through a same-named member of some other type is
// counted live. That is the correct direction for a gate to be wrong in: this
// tool will under-report, and everything it does report is worth reading.
var mentionsOf = new Dictionary<string, HashSet<string>>();   // member name -> names in its body
foreach (var tree in coreTrees)
    foreach (var node in tree.GetRoot().DescendantNodes())
    {
        string? owner = node switch
        {
            MethodDeclarationSyntax m => m.Identifier.Text,
            PropertyDeclarationSyntax p => p.Identifier.Text,
            ConstructorDeclarationSyntax c => c.Identifier.Text,
            _ => null,
        };
        if (owner == null) continue;
        if (!mentionsOf.TryGetValue(owner, out var set))
            mentionsOf[owner] = set = new HashSet<string>();
        foreach (var n in node.DescendantNodes().OfType<SimpleNameSyntax>())
            set.Add(n.Identifier.Text);
    }

// Field and property INITIALISERS run whenever the type is constructed, and a
// table built at static-init time — `Arsenal.Table` — is the way half of this
// codebase's data reaches the game. Treat the type itself as the owner.
foreach (var tree in coreTrees)
    foreach (var f in tree.GetRoot().DescendantNodes().OfType<FieldDeclarationSyntax>())
        foreach (var v in f.Declaration.Variables.Where(v => v.Initializer != null))
        {
            if (!mentionsOf.TryGetValue(v.Identifier.Text, out var set))
                mentionsOf[v.Identifier.Text] = set = new HashSet<string>();
            foreach (var n in v.Initializer!.DescendantNodes().OfType<SimpleNameSyntax>())
                set.Add(n.Identifier.Text);
        }

var live = new HashSet<string>(mentionsOf.Keys.Where(k => mentioned.Contains(k)));
// A type the Game constructs runs its constructors and initialisers.
foreach (var t in coreTypes.Where(mentioned.Contains)) live.Add(t);
var queue = new Queue<string>(live);
while (queue.Count > 0)
{
    var name = queue.Dequeue();
    if (!mentionsOf.TryGetValue(name, out var outgoing)) continue;
    foreach (var next in outgoing)
        if (mentionsOf.ContainsKey(next) && live.Add(next))
            queue.Enqueue(next);
}

// ------------------------------------------------------------------ allowlist

// EVERY ENTRY CARRIES A REASON, and the reason is the point. An allowlist of
// bare names is a mute button; an allowlist where somebody had to type why is
// a record of decisions. A reason shorter than fifteen characters is not one.
var allow = new Dictionary<string, string>();
if (allowPath != null && File.Exists(allowPath))
{
    using var doc = JsonDocument.Parse(File.ReadAllText(allowPath));
    foreach (var e in doc.RootElement.GetProperty("allow").EnumerateObject())
        allow[e.Name] = e.Value.GetString() ?? "";
}
var thin = allow.Where(kv => kv.Value.Trim().Length < 15).Select(kv => kv.Key).ToList();

// --------------------------------------------------------------------- verdict

var graded = api.Select(a =>
{
    string grade = qualified.Contains((a.Type, a.Name)) || qualified.Contains((a.Name, a.Name))
                   || (a.Kind == "type" && mentioned.Contains(a.Name))
        ? "strong"
        : mentioned.Contains(a.Name) ? "weak" : "none";
    bool inTests = testNames.Contains(a.Name);
    return (a.Kind, a.Type, a.Name, a.File, a.Line, Grade: grade, InTests: inTests,
            InCore: live.Contains(a.Name), Key: a.Type + "." + a.Name);
}).OrderBy(a => a.File).ThenBy(a => a.Line).ToList();

int strong = graded.Count(g => g.Grade == "strong");
int weak = graded.Count(g => g.Grade == "weak");
var none = graded.Where(g => g.Grade == "none").ToList();

// THE GATED CLASS, and only this one.
//
//   behaviour        a method or a property. Fields and types are state and
//                    vocabulary; a data record's field being unnamed by the
//                    Game is not a defect and gating on it teaches nobody
//                    anything. They stay in `--series` as a report.
//   the game never   `none`, which is a fact rather than an inference.
//   names it
//   the tests do     somebody wrote it, proved it works, and stopped. This is
//                    the whole incident, and it is the difference between dead
//                    code (delete it) and a disconnected feature (wire it).
//   nothing live     no chain of calls from anything the Game names reaches
//   in Core reaches  it. A helper called by a running method IS running, which
//   it               is why this is a graph walk and not a grep.
var behavioural = none.Where(g => g.Kind is "method" or "property").ToList();
var disconnected = behavioural.Where(g => g.InTests && !g.InCore).ToList();
var deadish = behavioural.Where(g => !g.InTests && !g.InCore).ToList();
bool Excused((string Kind, string Type, string Name, string File, int Line, string Grade,
              bool InTests, bool InCore, string Key) g)
    => allow.ContainsKey(g.Key) || allow.ContainsKey(g.Name);
var unwired = disconnected.Concat(deadish).Where(g => !Excused(g))
                          .OrderBy(g => g.File).ThenBy(g => g.Line).ToList();
var excused = disconnected.Count + deadish.Count - unwired.Count;

// A LEDGER THAT IS NEVER PAID DOWN IS A MUTE BUTTON WITH A GOOD CONSCIENCE.
// The entry has to come out when the API gets wired, and nothing but this
// check will make that happen — the build stays green either way, which is
// exactly the condition under which the roadmap grew a four-day-stale STILL
// OPEN list that I then read out as current.
var stillOwed = new HashSet<string>(disconnected.Concat(deadish).SelectMany(g => new[] { g.Key, g.Name }));
var stale = allow.Keys.Where(k => !stillOwed.Contains(k)).ToList();

// THE SERIES, FIRST, BEFORE ANY THRESHOLD. `nightNotDarker` was set to 0.135
// from a single frame pair and failed at 0.136 the next day. Nothing here gets
// a number that was not read off this output first.
if (series)
{
    foreach (var g in graded)
        Console.WriteLine($"{g.Grade,-6} {(g.InTests ? "T" : "-")}{(g.InCore ? "C" : "-")} "
                          + $"{g.Kind,-8} {g.Key,-44} {g.File}:{g.Line}");
    Console.WriteLine();
}

Console.WriteLine($"reach-check — {api.Count} public Core APIs, {gameDeclares.Count} names declared in Game");
Console.WriteLine($"  strong  {strong,4}   named with their declaring type at a Game call site");
Console.WriteLine($"  weak    {weak,4}   the name occurs, the receiver's type is unknowable here");
Console.WriteLine($"  none    {none.Count,4}   the name does not occur in the Game layer at all");
Console.WriteLine($"           of which {behavioural.Count} are methods or properties "
                  + $"({none.Count - behavioural.Count} fields and types, reported not gated)");
Console.WriteLine($"  GATED   {disconnected.Count,4}   tested, and no caller in Game or elsewhere in Core"
                  + $"  — built is not running");
Console.WriteLine($"          {deadish.Count,4}   no caller anywhere, tests included — dead"
                  + (excused > 0 ? $"   ({excused} allowlisted)" : ""));

if (thin.Count > 0)
{
    Console.WriteLine();
    Console.WriteLine($"  {thin.Count} allowlist entr{(thin.Count == 1 ? "y" : "ies")} with no real reason:");
    foreach (var k in thin) Console.WriteLine($"    {k}");
}

if (stale.Count > 0)
{
    Console.WriteLine();
    Console.WriteLine($"PAID OFF — {stale.Count} ledger entr{(stale.Count == 1 ? "y" : "ies")} "
                      + "now reached. Delete them; the ledger only counts down:");
    foreach (var k in stale.OrderBy(k => k)) Console.WriteLine($"  {k}");
}

if (unwired.Count > 0)
{
    Console.WriteLine();
    Console.WriteLine($"UNREACHED — {unwired.Count} behavioural Core API(s) with no caller:");
    foreach (var g in unwired)
        Console.WriteLine($"  {(g.InTests ? "tested, unwired" : "dead          "),-15} "
                          + $"{g.Kind,-8} {g.Key,-40} {g.File}:{g.Line}");
}

if (jsonOut != null)
{
    var payload = new
    {
        total = api.Count,
        strong,
        weak,
        none = none.Count,
        behavioural = behavioural.Count,
        disconnected = disconnected.Count,
        dead = deadish.Count,
        unwired = unwired.Select(g => new { g.Kind, g.Type, g.Name, g.File, g.Line, g.InTests }).ToList(),
    };
    File.WriteAllText(jsonOut, JsonSerializer.Serialize(payload,
        new JsonSerializerOptions { WriteIndented = true }));
}

bool ok = unwired.Count == 0 && thin.Count == 0 && stale.Count == 0;
if (!quiet)
{
    Console.WriteLine();
    Console.WriteLine(ok
        ? $"reach ok — {allow.Count} on the ledger, 0 unexplained"
        : $"reach FAILED — {unwired.Count} unreached, {stale.Count} stale ledger entries, "
          + $"{thin.Count} without a reason");
}
return ok ? 0 : 1;
