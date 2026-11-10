// Compile alongside Setup.cs with /main:SetupChecks. All writes stay in the supplied fixture root.
using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
internal static class SetupChecks {
    private static Type Subject = typeof(Setup);
    private static object Call(string name, params object[] args) {
        try { return Subject.GetMethod(name, BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, args); }
        catch (TargetInvocationException error) { throw error.InnerException; }
    }
    private static void Check(bool yes, string name) { if (!yes) throw new Exception(name); Console.WriteLine("PASS " + name); }
    private static bool Refused(Action action) { try { action(); return false; } catch (IOException) { return true; } }
    [STAThread] public static int Main(string[] args) {
        string root = Path.GetFullPath(args[0]);
        string container = Path.Combine(root, "install"), program = Path.Combine(container, "program");
        Subject.GetField("Container", BindingFlags.NonPublic | BindingFlags.Static).SetValue(null, container);
        Subject.GetField("Program", BindingFlags.NonPublic | BindingFlags.Static).SetValue(null, program);
        Directory.CreateDirectory(program);File.WriteAllText(Path.Combine(program,"keep.txt"),"saved program");
        string outside = Path.Combine(root,"outside","keep.txt");
        FileAttributes attributes = File.GetAttributes(outside);
        Call("RemoveTree",Path.Combine(root,"stage"));
        Check(!Directory.Exists(Path.Combine(root,"stage")) && File.ReadAllText(outside)=="saved outside" && File.GetAttributes(outside)==attributes,"cleanup leaves junction target and attributes intact");
        Check(Refused(delegate { Call("RejectLinkedDirectory",Path.Combine(root,"linked-root")); }),"linked installation root refused");
        Call("RemoveTree",Path.Combine(root,"linked-root"));
        Check(File.Exists(outside),"removing root junction leaves target intact");
        bool nested=false;
        int result=(int)Call("WithInstallLock",new Func<int>(delegate {
            Check(File.Exists(Path.Combine(container,".pler-setup.lock")),"setup lease held during operation");
            Check(Refused(delegate { Call("WithInstallLock",new Func<int>(delegate { nested=true; return 0; })); }),"second operation rejected before work");return 42;
        }));
        Check(result==42 && !nested && !File.Exists(Path.Combine(container,".pler-setup.lock")),"setup lease released after success");
        try { Call("WithInstallLock",new Func<int>(delegate { throw new InvalidOperationException("invented failure"); })); } catch (InvalidOperationException) { }
        Check(!File.Exists(Path.Combine(container,".pler-setup.lock")),"setup lease released after failure");
        string running=Path.Combine(program,".pler-running.lock");
        using(FileStream app=new FileStream(running,FileMode.OpenOrCreate,FileAccess.Read,FileShare.ReadWrite))
            Check(Refused(delegate { Call("MoveAside",null,true); }) && File.Exists(Path.Combine(program,"keep.txt")),"running app blocks replacement without moving files");
        string old=(string)Call("MoveAside",null,true);
        Check(!Directory.Exists(program) && File.ReadAllText(Path.Combine(old,"keep.txt"))=="saved program","closed app can move after lease check");
        Call("RemoveTree",old);
        using(FileStream lockfile=new FileStream(Path.Combine(container,".pler-setup.lock"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None))
            Check(Refused(delegate { Call("WithInstallLock",new Func<int>(delegate { return 0; })); }),"external file owner blocks setup");
        File.Delete(Path.Combine(container,".pler-setup.lock"));
        Console.WriteLine("Setup checks completed without installation or registry writes");return 0;
    }
}
