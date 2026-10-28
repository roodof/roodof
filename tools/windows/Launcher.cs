using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

[assembly: AssemblyTitle("PLER")]
[assembly: AssemblyProduct("PLER")]
[assembly: AssemblyDescription("Local agent usage viewer")]

internal static class Launcher {
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
            string runtime = Path.Combine(folder, "runtime", "python.exe");
            string entry = Path.Combine(folder, "app", "start.py");
            if (!File.Exists(runtime) || !File.Exists(entry))
                throw new IOException("Extract the complete PLER folder before opening the application.");
            StringBuilder command = new StringBuilder("-I -S " + Quote(entry));
            foreach (string argument in check ? new string[] { "--version" } : args)
                command.Append(' ').Append(Quote(argument));
            ProcessStartInfo info = new ProcessStartInfo(runtime, command.ToString());
            info.WorkingDirectory = folder;
            info.UseShellExecute = false;
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
        } catch (Exception error) {
            if (!check) MessageBox.Show(error.Message, "PLER", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
