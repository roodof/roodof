using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.Text.RegularExpressions;
using System.Windows.Forms;

[assembly: AssemblyTitle("PLER")]
[assembly: AssemblyProduct("PLER")]
[assembly: AssemblyDescription("Local agent usage viewer")]

internal static class Launcher {
    private static string VersionWord(string value) {
        value = value.Trim();
        if (!Regex.IsMatch(value, @"\A(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\z"))
            throw new IOException("The installed version selection is invalid.");
        return value;
    }
    private static string Pointer(string folder) {
        string path = Path.Combine(folder, ".pler-current");
        if (!File.Exists(path)) return null;
        if (new FileInfo(path).Length > 64) throw new IOException("The installed version selection is invalid.");
        return VersionWord(File.ReadAllText(path));
    }
    private static string Selected(string folder, string version) {
        string selected = version == null ? folder : Path.Combine(folder, ".pler-versions", version);
        if (!File.Exists(Path.Combine(selected, "runtime", "python.exe")) || !File.Exists(Path.Combine(selected, "app", "start.py")))
            throw new IOException("The selected PLER version is incomplete. Keep your data and reinstall the complete package.");
        return selected;
    }
    private static void WritePointer(string folder, string version) {
        string path = Path.Combine(folder, ".pler-current");
        if (version == null) { if (File.Exists(path)) File.Delete(path); return; }
        string temp = Path.Combine(folder, ".pler-pointer-" + Guid.NewGuid().ToString("N"));
        byte[] data = Encoding.ASCII.GetBytes(VersionWord(version) + "\n");
        using (FileStream file = new FileStream(temp, FileMode.CreateNew, FileAccess.Write)) { file.Write(data, 0, data.Length); file.Flush(true); }
        if (File.Exists(path)) File.Replace(temp, path, null); else File.Move(temp, path);
    }
    private static FileStream Lease(string folder, bool exclusive) {
        return new FileStream(Path.Combine(folder, ".pler-running.lock"), exclusive ? FileMode.OpenOrCreate : FileMode.Open, exclusive ? FileAccess.ReadWrite : FileAccess.Read,
                              exclusive ? FileShare.None : FileShare.ReadWrite);
    }
    private static void Recover(string folder) {
        string pending = Path.Combine(folder, ".pler-pending");
        if (!File.Exists(pending)) return;
        using (FileStream lease = Lease(folder, true)) {
            if (new FileInfo(pending).Length > 128) throw new IOException("PLER recovery needs inspection.");
            string[] lines = File.ReadAllLines(pending);
            if (lines.Length != 2) throw new IOException("PLER recovery needs inspection.");
            string next = VersionWord(lines[0]), old = lines[1] == "base" ? null : VersionWord(lines[1]);
            string current = Pointer(folder);
            if (current != next && current != old) throw new IOException("PLER recovery needs inspection.");
            Selected(folder, old); WritePointer(folder, old); File.Delete(pending);
        }
    }
    // PLER-Setup lists the installed version under Settings > Apps. An in-app update switches the
    // version without the installer, so keep that one value current. Only an entry that already
    // points at this installation is touched; a portable folder writes nothing.
    private static void SyncListedVersion(string folder, string version) {
        try {
            if (version == null) {
                Match found = Regex.Match(File.ReadAllText(Path.Combine(folder, "manifest.json")), @"""version""\s*:\s*""([0-9.]{1,20})""");
                if (!found.Success) return;
                version = VersionWord(found.Groups[1].Value);
            }
            using (Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(
                       @"Software\Microsoft\Windows\CurrentVersion\Uninstall\PLER", true)) {
                if (key == null) return;
                string location = key.GetValue("InstallLocation") as string;
                if (location == null || !string.Equals(Path.GetFullPath(location).TrimEnd('\\'),
                        Path.GetDirectoryName(folder), StringComparison.OrdinalIgnoreCase)) return;
                if (key.GetValue("DisplayVersion") as string != version) key.SetValue("DisplayVersion", version);
            }
        } catch { }
    }
    // Quote a Windows argv value without passing through cmd or another shell.
    private static string Quote(string value) {
        StringBuilder result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char item in value) {
            if (item == '\\') { slashes++; continue; }
            if (item == '"') {
                result.Append('\\', slashes * 2 + 1).Append(item);
            } else {
                result.Append('\\', slashes).Append(item);
            }
            slashes = 0;
        }
        return result.Append('\\', slashes * 2).Append('"').ToString();
    }

    [STAThread]
    public static int Main(string[] args) {
        bool check = args.Length == 1 && args[0] == "--self-check";
        try {
            string folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            Recover(folder);
            using (FileStream lease = Lease(folder, false)) {
            string current = Pointer(folder);
            string selected = Selected(folder, current);
            if (!check) SyncListedVersion(folder, current);
            string runtime = Path.Combine(selected, "runtime", "python.exe");
            string entry = Path.Combine(selected, "app", "start.py");
            if (!File.Exists(runtime) || !File.Exists(entry))
                throw new IOException("Extract the complete PLER folder before opening the application.");
            StringBuilder command = new StringBuilder("-I -S " + Quote(entry));
            foreach (string argument in check ? new string[] { "--version" } : args)
                command.Append(' ').Append(Quote(argument));
            // The portable GUI always opens its own window. Terminal commands use PLER.cmd.
            if (!check && (args.Length == 0 || args[0] == "demo" || args[0].StartsWith("--")) &&
                Array.IndexOf(args, "--version") < 0 && Array.IndexOf(args, "--help") < 0 &&
                Array.IndexOf(args, "--desktop") < 0)
                command.Append(" --desktop");
            ProcessStartInfo info = new ProcessStartInfo(runtime, command.ToString());
            info.WorkingDirectory = folder;
            info.UseShellExecute = false;
            info.EnvironmentVariables["PLER_LAUNCHER_PID"] = Process.GetCurrentProcess().Id.ToString();
            info.EnvironmentVariables["PLER_INSTALL_ROOT"] = folder;
            info.CreateNoWindow = true;
            info.RedirectStandardOutput = true;
            info.RedirectStandardError = true;
            using (Process process = Process.Start(info)) {
                Task<string> output = process.StandardOutput.ReadToEndAsync();
                Task<string> error = process.StandardError.ReadToEndAsync();
                process.WaitForExit();
                Task.WaitAll(output, error);
                if (check) return process.ExitCode == 0 && output.Result.Trim().StartsWith("PLER ") ? 0 : 1;
                if (process.ExitCode != 0)
                    MessageBox.Show("PLER could not start. The original agent logs were not changed.\n\n" +
                        error.Result, "PLER", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return process.ExitCode;
            }
            }
        } catch (Exception error) {
            if (!check) MessageBox.Show(error.Message, "PLER", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
