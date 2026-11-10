// Roodof per-user installer and uninstaller (one source, compiled twice by tools/build_windows_setup.py).
// Install: no questions, no administrator rights. The verified package goes to
// %LOCALAPPDATA%\Programs\Roodof\program; Start menu and desktop shortcuts and a per-user Apps entry
// are written, then Roodof opens. Saved Roodof history (%LOCALAPPDATA%\pler) is never touched by install.
// The in-app updater keeps working: it stages beside the program folder, inside the Roodof folder.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Roodof Setup")]
[assembly: AssemblyProduct("Roodof")]
[assembly: AssemblyCompany("Roodof")]
[assembly: AssemblyDescription("Installs Roodof for the current user")]

internal static class Setup {
    private const string AppId = "PLER.Desktop";
    private static readonly Guid ToastClsid = new Guid("1322F0A3-7DC3-4840-9336-2EFD311DF888");
    private const string Payload = "pler-package.zip";
    private const string UninstallerResource = "pler-uninstall.exe";
    private const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\PLER";
    private static readonly bool Turkish = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName == "tr";
    private static readonly string Container = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "PLER");
    private static readonly string Program = Path.Combine(Container, "program");
    private static readonly string Uninstaller = Path.Combine(Container, "Uninstall Roodof.exe");
    private static readonly string History = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "pler");
    private static readonly string StartLink = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Roodof.lnk");
    private static readonly string DesktopLink = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "Roodof.lnk");

    private static string T(string english, string turkish) { return Turkish ? turkish : english; }

    [DllImport("user32.dll")] private static extern bool SetProcessDPIAware();

    [STAThread]
    public static int Main(string[] args) {
        bool quiet = Array.IndexOf(args, "/quiet") >= 0;
        try { SetProcessDPIAware(); } catch (Exception) { }
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        try {
            bool hasPayload = Assembly.GetExecutingAssembly().GetManifestResourceInfo(Payload) != null;
            if (args.Length > 0 && args[0] == "/uninstall-run") return UninstallRun(args, quiet);
            if (!hasPayload || Array.IndexOf(args, "/uninstall") >= 0) return UninstallStart(quiet);
            return Install(Array.IndexOf(args, "/no-launch") >= 0, quiet);
        } catch (Exception error) {
            if (!quiet) MessageBox.Show(error.Message, "Roodof", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    // ---------- versions ----------
    private static int[] Version(string value) {
        if (value == null) return null;
        Match match = Regex.Match(value.Trim(), @"\A(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\z");
        if (!match.Success) return null;
        return new int[] { int.Parse(match.Groups[1].Value), int.Parse(match.Groups[2].Value), int.Parse(match.Groups[3].Value) };
    }
    private static int Compare(int[] a, int[] b) {
        for (int i = 0; i < 3; i++) if (a[i] != b[i]) return a[i] < b[i] ? -1 : 1;
        return 0;
    }
    private static string Text(int[] v) { return v[0] + "." + v[1] + "." + v[2]; }

    private static Dictionary<string, object> Json(string text) {
        JavaScriptSerializer reader = new JavaScriptSerializer();
        reader.MaxJsonLength = 16 * 1024 * 1024;
        Dictionary<string, object> value = reader.DeserializeObject(text) as Dictionary<string, object>;
        if (value == null) throw new InvalidDataException("invalid manifest");
        return value;
    }

    // The version that actually runs: an in-app update selects .pler-versions\VERSION via .pler-current.
    private static int[] Installed() {
        try {
            string manifest = Path.Combine(Program, "manifest.json");
            if (!File.Exists(manifest) || !File.Exists(Path.Combine(Program, "PLER.exe"))) return null;
            int[] baseline = Version(Json(File.ReadAllText(manifest))["version"] as string);
            if (baseline == null) return null;
            string pointer = Path.Combine(Program, ".pler-current");
            if (File.Exists(pointer) && new FileInfo(pointer).Length <= 64) {
                int[] selected = Version(File.ReadAllText(pointer));
                if (selected != null && File.Exists(Path.Combine(Program, ".pler-versions", Text(selected), "runtime", "python.exe")))
                    return selected;
            }
            return baseline;
        } catch (Exception) { return null; }
    }

    // ---------- window ----------
    private static int Scaled(int value) {
        using (Graphics graphics = Graphics.FromHwnd(IntPtr.Zero)) return (int)Math.Round(value * graphics.DpiX / 96f);
    }
    // One padded column that sizes itself to its contents, so text is never clipped at any scale.
    private static TableLayoutPanel Stack(params Control[] items) {
        TableLayoutPanel panel = new TableLayoutPanel();
        panel.ColumnCount = 1; panel.AutoSize = true; panel.AutoSizeMode = AutoSizeMode.GrowAndShrink;
        panel.Padding = new Padding(Scaled(20)); panel.Dock = DockStyle.Fill;
        foreach (Control item in items) panel.Controls.Add(item);
        return panel;
    }

    private sealed class Window : Form {
        public readonly Label Message = new Label();
        public readonly ProgressBar Bar = new ProgressBar();
        public bool Busy = true;
        public Window(string message) {
            Text = "Roodof";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false; MinimizeBox = false; ShowInTaskbar = true;
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9.75f);
            AutoSize = true; AutoSizeMode = AutoSizeMode.GrowAndShrink;
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }
            Message.AutoSize = true; Message.Text = message; Message.Margin = new Padding(0, 0, 0, 12);
            Bar.Minimum = 0; Bar.Maximum = 1000; Bar.Size = new Size(Scaled(360), Scaled(18));
            Controls.Add(Stack(Message, Bar));
            FormClosing += delegate(object sender, FormClosingEventArgs e) {
                if (Busy && e.CloseReason == CloseReason.UserClosing) e.Cancel = true;
            };
        }
        public void Say(string message) { Invoke((MethodInvoker)delegate { Message.Text = message; }); }
        public void Fraction(double value) {
            int position = (int)Math.Max(0, Math.Min(1000, value * 1000));
            BeginInvoke((MethodInvoker)delegate { Bar.Value = position; });
        }
        public DialogResult Ask(string text, MessageBoxButtons buttons, MessageBoxIcon icon) {
            DialogResult answer = DialogResult.Cancel;
            Invoke((MethodInvoker)delegate { answer = MessageBox.Show(this, text, "Roodof", buttons, icon); });
            return answer;
        }
    }

    // Runs work on a background thread while a small window shows progress; quiet runs show nothing.
    private static int WithWindow(string message, bool quiet, Func<Window, int> work) {
        if (quiet) return work(null);
        Window window = new Window(message);
        int result = 1;
        window.Shown += delegate {
            Thread thread = new Thread(delegate() {
                try { result = work(window); }
                catch (Exception error) { result = 1; window.Ask(error.Message, MessageBoxButtons.OK, MessageBoxIcon.Error); }
                window.Invoke((MethodInvoker)delegate { window.Busy = false; window.Close(); });
            });
            thread.IsBackground = true;
            thread.Start();
        };
        Application.Run(window);
        return result;
    }

    // ---------- files ----------
    private static void RemoveTree(string path) {
        if (!Directory.Exists(path)) return;
        for (int attempt = 0; ; attempt++) {
            try { RemoveDirectory(new DirectoryInfo(path)); return; }
            catch (IOException) { if (attempt >= 4) throw; Thread.Sleep(500); }
            catch (UnauthorizedAccessException) { if (attempt >= 4) throw; Thread.Sleep(500); }
        }
    }
    // Junctions/symlinks belong to the installation, their targets do not.
    private static void RemoveDirectory(DirectoryInfo directory) {
        if ((directory.Attributes & FileAttributes.ReparsePoint) != 0) { directory.Delete(); return; }
        foreach (FileSystemInfo entry in directory.GetFileSystemInfos()) {
            DirectoryInfo child = entry as DirectoryInfo;
            if (child != null) RemoveDirectory(child);
            else {
                if ((entry.Attributes & FileAttributes.ReparsePoint) == 0) entry.Attributes = FileAttributes.Normal;
                entry.Delete();
            }
        }
        directory.Delete();
    }
    private static void RejectLinkedDirectory(string path) {
        if (Directory.Exists(path) && (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0)
            throw new IOException(T("The Roodof installation folder is a linked directory. Keep its contents and choose a normal installation folder.",
                "Roodof kurulum klasörü bağlantılı bir klasör. İçeriğini koruyun ve normal bir kurulum klasörü kullanın."));
    }
    // Hold across extraction, cleanup, replacement and registration, including uninstall.
    private static int WithInstallLock(Func<int> work) {
        RejectLinkedDirectory(Container);
        Directory.CreateDirectory(Container);
        RejectLinkedDirectory(Program);
        string path = Path.Combine(Container, ".pler-setup.lock");
        FileStream lease;
        try { lease = new FileStream(path, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None); }
        catch (IOException) { throw new IOException(T("Another Roodof setup is running. Wait for it to finish and try again.",
            "Başka bir Roodof kurulumu çalışıyor. Bitmesini bekleyip yeniden deneyin.")); }
        try { return work(); }
        finally {
            lease.Dispose();
            try { File.Delete(path); } catch (IOException) { } catch (UnauthorizedAccessException) { }
            try { if (Directory.GetFileSystemEntries(Container).Length == 0) Directory.Delete(Container); } catch (IOException) { } catch (UnauthorizedAccessException) { }
        }
    }
    private static void TryRemoveTree(string path) { try { RemoveTree(path); } catch (Exception) { } }

    private static void CleanLeftovers() {
        if (!Directory.Exists(Container)) return;
        foreach (string folder in Directory.GetDirectories(Container)) {
            string name = Path.GetFileName(folder);
            if (name.StartsWith(".pler-setup-") || name.StartsWith(".pler-old-")) TryRemoveTree(folder);
        }
    }

    // An in-app update holds a guard file with its process id beside the program folder.
    private static bool UpdateRunning() {
        if (!Directory.Exists(Container)) return false;
        foreach (string guard in Directory.GetFiles(Container, ".pler-update-*.lock")) {
            try {
                if (new FileInfo(guard).Length > 32) return true;
                int pid = int.Parse(File.ReadAllText(guard).Trim(), CultureInfo.InvariantCulture);
                using (Process process = Process.GetProcessById(pid)) { if (!process.HasExited) return true; }
            } catch (ArgumentException) { } catch (FormatException) { return true; } catch (IOException) { return true; }
        }
        return false;
    }

    // A running Roodof keeps files in the program folder open, so the folder cannot be renamed.
    private static string MoveAside(Window window, bool quiet) {
        string old = Path.Combine(Container, ".pler-old-" + Guid.NewGuid().ToString("N"));
        while (true) {
            try {
                // Check the same lease the launcher/updater holds. Close our probe before the
                // rename: Windows refuses a parent-directory move while this handle is open.
                using (FileStream lease = new FileStream(Path.Combine(Program, ".pler-running.lock"),
                           FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None)) { }
                Directory.Move(Program, old); return old;
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
            if (quiet || window == null) throw new IOException(T("Roodof is open. Close it and try again.", "Roodof açık. Kapatıp yeniden deneyin."));
            DialogResult answer = window.Ask(T("Roodof is open. Close the Roodof window, then select Retry.",
                "Roodof açık. Roodof penceresini kapatın, sonra Yeniden Dene'yi seçin."), MessageBoxButtons.RetryCancel, MessageBoxIcon.Information);
            if (answer != DialogResult.Retry) return null;
        }
    }

    private static string Relative(string name, string top) {
        if (!name.StartsWith(top + "/")) throw new InvalidDataException("unexpected package layout");
        string relative = name.Substring(top.Length + 1);
        if (relative.Length == 0 || relative.Contains("\\") || relative.Contains(":") || relative.StartsWith("/"))
            throw new InvalidDataException("unsafe package path");
        foreach (string part in relative.Split('/'))
            if (part.Length == 0 || part == "." || part == "..") throw new InvalidDataException("unsafe package path");
        return relative;
    }

    // Extracts the embedded package into a new folder and checks every file against manifest.json.
    private static int[] Extract(string stage, Window window) {
        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(Payload))
        using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read)) {
            if (archive.Entries.Count == 0) throw new InvalidDataException("empty package");
            string top = archive.Entries[0].FullName.Split('/')[0];
            ZipArchiveEntry manifestEntry = archive.GetEntry(top + "/manifest.json");
            if (manifestEntry == null || manifestEntry.Length > 4 * 1024 * 1024) throw new InvalidDataException("missing manifest");
            Dictionary<string, object> manifest;
            using (StreamReader reader = new StreamReader(manifestEntry.Open(), Encoding.UTF8)) manifest = Json(reader.ReadToEnd());
            int[] version = Version(manifest["version"] as string);
            Dictionary<string, object> hashes = manifest["files"] as Dictionary<string, object>;
            if (version == null || hashes == null || (manifest["platform"] as string) != "windows-x64")
                throw new InvalidDataException("invalid manifest");
            long total = 0, done = 0;
            foreach (ZipArchiveEntry entry in archive.Entries) total += entry.Length;
            DriveInfo drive = new DriveInfo(Path.GetPathRoot(stage));
            if (drive.AvailableFreeSpace < total + 256L * 1024 * 1024)
                throw new IOException(T("There is not enough free disk space to install Roodof.", "Roodof'i kurmak için yeterli boş disk alanı yok."));
            HashSet<string> seen = new HashSet<string>();
            byte[] buffer = new byte[1 << 20];
            foreach (ZipArchiveEntry entry in archive.Entries) {
                if (entry.FullName.EndsWith("/")) continue;
                string relative = Relative(entry.FullName, top);
                if (!seen.Add(relative)) throw new InvalidDataException("duplicate package path");
                bool isManifest = relative == "manifest.json";
                if (!isManifest && !hashes.ContainsKey(relative)) throw new InvalidDataException("file missing from manifest: " + relative);
                string target = Path.Combine(stage, relative.Replace('/', Path.DirectorySeparatorChar));
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                using (SHA256 sha = SHA256.Create())
                using (Stream input = entry.Open())
                using (FileStream output = new FileStream(target, FileMode.CreateNew, FileAccess.Write)) {
                    int count;
                    while ((count = input.Read(buffer, 0, buffer.Length)) > 0) {
                        sha.TransformBlock(buffer, 0, count, null, 0);
                        output.Write(buffer, 0, count);
                        done += count;
                        if (window != null) window.Fraction(total == 0 ? 1 : (double)done / total);
                    }
                    sha.TransformFinalBlock(buffer, 0, 0);
                    string digest = BitConverter.ToString(sha.Hash).Replace("-", "").ToLowerInvariant();
                    if (!isManifest && digest != (hashes[relative] as string))
                        throw new InvalidDataException("package file changed: " + relative);
                }
            }
            foreach (string name in hashes.Keys)
                if (!seen.Contains(name)) throw new InvalidDataException("package file missing: " + name);
            return version;
        }
    }

    private static void SelfCheck(string folder) {
        ProcessStartInfo info = new ProcessStartInfo(Path.Combine(folder, "PLER.exe"), "--self-check");
        info.UseShellExecute = false; info.CreateNoWindow = true; info.WorkingDirectory = folder;
        using (Process process = Process.Start(info)) {
            if (!process.WaitForExit(180000)) { try { process.Kill(); } catch (Exception) { } throw new IOException("package check timed out"); }
            if (process.ExitCode != 0) throw new IOException(T("The Roodof package could not start. Nothing was changed.",
                "Roodof paketi başlatılamadı. Hiçbir şey değiştirilmedi."));
        }
    }

    // ---------- shortcuts ----------
    [ComImport, Guid("00021401-0000-0000-C000-000000000046")] private class ShellLink { }
    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("000214F9-0000-0000-C000-000000000046")]
    private interface IShellLinkW {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder file, int size, IntPtr data, int flags);
        void GetIDList(out IntPtr list);
        void SetIDList(IntPtr list);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder name, int size);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string name);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder dir, int size);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string dir);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder args, int size);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string args);
        void GetHotkey(out short key);
        void SetHotkey(short key);
        void GetShowCmd(out int show);
        void SetShowCmd(int show);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder path, int size, out int index);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string path, int index);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string path, int reserved);
        void Resolve(IntPtr window, int flags);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string file);
    }
    [StructLayout(LayoutKind.Sequential, Pack = 4)] private struct PropertyKey { public Guid Format; public uint Id; }
    [StructLayout(LayoutKind.Sequential)] private struct PropVariant { public ushort Type; public ushort R1, R2, R3; public IntPtr Value; public IntPtr Extra; }
    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
    private interface IPropertyStore {
        void GetCount(out uint count);
        void GetAt(uint index, out PropertyKey key);
        void GetValue(ref PropertyKey key, IntPtr value);
        void SetValue(ref PropertyKey key, ref PropVariant value);
        void Commit();
    }

    // The shortcut carries the window's AppUserModelID so a pinned button and the open window group as one.
    // The Start shortcut is written exactly as Electron keeps its notification shortcut (named after
    // the window process's product name, targeting that process, which hands over to PLER.exe), so
    // Electron finds it valid and adds no second entry. The desktop shortcut opens PLER.exe directly.
    private static void Shortcut(string path, string target) {
        string launcher = Path.Combine(Program, "PLER.exe");
        IShellLinkW link = (IShellLinkW)new ShellLink();
        link.SetPath(target);
        link.SetWorkingDirectory(Path.GetDirectoryName(target));
        link.SetIconLocation(launcher, 0);
        link.SetDescription(T("Local agent usage viewer", "Yerel ajan kullanım görüntüleyici"));
        IPropertyStore store = (IPropertyStore)link;
        PropertyKey key = new PropertyKey { Format = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"), Id = 5 };
        PropVariant value = new PropVariant { Type = 31, Value = Marshal.StringToCoTaskMemUni(AppId) };
        // Same toast CLSID as desktop/main.cjs, so Electron finds this shortcut and adds none of its own.
        PropertyKey toastKey = new PropertyKey { Format = key.Format, Id = 26 };
        PropVariant toast = new PropVariant { Type = 72, Value = Marshal.AllocCoTaskMem(16) };
        Marshal.Copy(ToastClsid.ToByteArray(), 0, toast.Value, 16);
        try { store.SetValue(ref key, ref value); store.SetValue(ref toastKey, ref toast); store.Commit(); }
        finally { Marshal.FreeCoTaskMem(value.Value); Marshal.FreeCoTaskMem(toast.Value); }
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        ((IPersistFile)link).Save(path, true);
        Marshal.ReleaseComObject(link);
    }

    private static long FolderKilobytes(string path) {
        long bytes = 0;
        foreach (string file in Directory.GetFiles(path, "*", SearchOption.AllDirectories)) bytes += new FileInfo(file).Length;
        return bytes / 1024;
    }

    private static void Register(int[] version) {
        Shortcut(StartLink, Path.Combine(Program, "desktop", "PLER-Desktop.exe"));
        Shortcut(DesktopLink, Path.Combine(Program, "Roodof.exe"));
        RemoveLegacyShortcut(Environment.SpecialFolder.Programs);
        RemoveLegacyShortcut(Environment.SpecialFolder.DesktopDirectory);
        using (RegistryKey key = Registry.CurrentUser.CreateSubKey(UninstallKey)) {
            key.SetValue("DisplayName", "Roodof");
            key.SetValue("DisplayVersion", Text(version));
            key.SetValue("Publisher", "Roodof");
            key.SetValue("DisplayIcon", "\"" + Path.Combine(Program, "PLER.exe") + "\",0");
            key.SetValue("InstallLocation", Container);
            key.SetValue("UninstallString", "\"" + Uninstaller + "\"");
            key.SetValue("QuietUninstallString", "\"" + Uninstaller + "\" /quiet");
            key.SetValue("InstallDate", DateTime.Now.ToString("yyyyMMdd", CultureInfo.InvariantCulture));
            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
            key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
            key.SetValue("EstimatedSize", (int)Math.Min(int.MaxValue, FolderKilobytes(Program)), RegistryValueKind.DWord);
        }
    }

    // Remove only a legacy shortcut that targets this exact installation. Never remove
    // a user's unrelated shortcut merely because its filename happens to be PLER.lnk.
    private static void RemoveLegacyShortcut(Environment.SpecialFolder location) {
        string old = Path.Combine(Environment.GetFolderPath(location), "PLER.lnk");
        if (!File.Exists(old) || (File.GetAttributes(old) & FileAttributes.ReparsePoint) != 0) return;
        IShellLinkW link = (IShellLinkW)new ShellLink();
        try {
            ((IPersistFile)link).Load(old, 0);
            StringBuilder target = new StringBuilder(32768);
            link.GetPath(target, target.Capacity, IntPtr.Zero, 0);
            string actual = Path.GetFullPath(target.ToString());
            if (string.Equals(actual, Path.Combine(Program, "PLER.exe"), StringComparison.OrdinalIgnoreCase)
                || string.Equals(actual, Path.Combine(Program, "desktop", "PLER-Desktop.exe"), StringComparison.OrdinalIgnoreCase))
                File.Delete(old);
        } catch (Exception) { /* A foreign or unreadable shortcut is preserved. */ }
        finally { Marshal.ReleaseComObject(link); }
    }

    private static void WriteUninstaller() {
        using (Stream input = Assembly.GetExecutingAssembly().GetManifestResourceStream(UninstallerResource)) {
            if (input == null) throw new InvalidDataException("missing uninstaller");
            string temp = Uninstaller + "." + Guid.NewGuid().ToString("N") + ".tmp";
            using (FileStream output = new FileStream(temp, FileMode.CreateNew, FileAccess.Write)) input.CopyTo(output);
            if (File.Exists(Uninstaller)) File.Delete(Uninstaller);
            File.Move(temp, Uninstaller);
        }
    }

    private static void Launch() {
        ProcessStartInfo info = new ProcessStartInfo(Path.Combine(Program, "Roodof.exe"));
        info.UseShellExecute = true; info.WorkingDirectory = Program;
        Process.Start(info).Dispose();
    }

    // ---------- install ----------
    private static int Install(bool noLaunch, bool quiet) {
        return WithInstallLock(delegate { return WithWindow(T("Installing Roodof…", "Roodof kuruluyor…"), quiet, delegate(Window window) {
            Directory.CreateDirectory(Container);
            CleanLeftovers();
            int[] installed = Installed();
            int[] packaged = PackagedVersion();
            if (installed != null && Compare(installed, packaged) >= 0) {
                // Same or newer (an in-app update may be ahead): keep it, repair shortcuts, open it.
                if (window != null) { window.Say(T("Opening Roodof…", "Roodof açılıyor…")); window.Fraction(1); }
                if (!File.Exists(Uninstaller)) WriteUninstaller();
                Register(installed);
                if (!noLaunch) Launch();
                return 0;
            }
            if (UpdateRunning()) throw new IOException(T("Roodof is installing an update. Try again when it finishes.",
                "Roodof bir güncelleme kuruyor. Bittiğinde yeniden deneyin."));
            string stage = Path.Combine(Container, ".pler-setup-" + Guid.NewGuid().ToString("N"));
            string old = null;
            try {
                Directory.CreateDirectory(stage);
                int[] version = Extract(stage, window);
                if (window != null) window.Say(T("Checking Roodof…", "Roodof denetleniyor…"));
                SelfCheck(stage);
                if (Directory.Exists(Program)) {
                    old = MoveAside(window, quiet);
                    if (old == null) { TryRemoveTree(stage); return 2; }
                }
                try { Directory.Move(stage, Program); }
                catch (Exception) { if (old != null) Directory.Move(old, Program); old = null; throw; }
                stage = null;
                if (old != null) TryRemoveTree(old);
                WriteUninstaller();
                Register(version);
                if (window != null) window.Say(T("Opening Roodof…", "Roodof açılıyor…"));
                if (!noLaunch) Launch();
                return 0;
            } finally {
                if (stage != null) TryRemoveTree(stage);
            }
        }); });
    }

    private static int[] PackagedVersion() {
        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(Payload))
        using (ZipArchive archive = new ZipArchive(stream, ZipArchiveMode.Read)) {
            string top = archive.Entries[0].FullName.Split('/')[0];
            ZipArchiveEntry entry = archive.GetEntry(top + "/manifest.json");
            if (entry == null) throw new InvalidDataException("missing manifest");
            using (StreamReader reader = new StreamReader(entry.Open(), Encoding.UTF8)) {
                int[] version = Version(Json(reader.ReadToEnd())["version"] as string);
                if (version == null) throw new InvalidDataException("invalid manifest");
                return version;
            }
        }
    }

    // ---------- uninstall ----------
    private static bool SamePath(string a, string b) {
        return string.Equals(Path.GetFullPath(a).TrimEnd('\\'), Path.GetFullPath(b).TrimEnd('\\'), StringComparison.OrdinalIgnoreCase);
    }

    // The uninstaller lives inside the folder it removes, so it continues from a temporary copy.
    private static int UninstallStart(bool quiet) {
        string self = Assembly.GetExecutingAssembly().Location;
        string temp = Path.Combine(Path.GetTempPath(), "pler-uninstall-" + Guid.NewGuid().ToString("N") + ".exe");
        File.Copy(self, temp);
        ProcessStartInfo info = new ProcessStartInfo(temp, "/uninstall-run " +
            Process.GetCurrentProcess().Id.ToString(CultureInfo.InvariantCulture) + (quiet ? " /quiet" : ""));
        info.UseShellExecute = false;
        Process.Start(info).Dispose();
        return 0;
    }

    private static bool Confirm(out bool removeHistory) {
        removeHistory = false;
        using (Form form = new Form()) {
            form.Text = T("Uninstall Roodof", "Roodof'i kaldır");
            form.FormBorderStyle = FormBorderStyle.FixedDialog;
            form.MaximizeBox = false; form.MinimizeBox = false;
            form.StartPosition = FormStartPosition.CenterScreen;
            form.Font = new Font("Segoe UI", 9.75f);
            form.AutoSize = true; form.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            try { form.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }
            Size wrap = new Size(Scaled(420), 0);
            Label message = new Label();
            message.AutoSize = true; message.MaximumSize = wrap; message.Margin = new Padding(0, 0, 0, Scaled(12));
            message.Text = T("Roodof will be removed from this computer. Your agent logs are not changed.",
                "Roodof bu bilgisayardan kaldırılacak. Ajan kayıtlarınız değişmez.");
            CheckBox history = new CheckBox();
            history.AutoSize = true; history.MaximumSize = wrap; history.Margin = new Padding(0, 0, 0, Scaled(16));
            history.Text = T("Also delete saved Roodof history", "Kayıtlı Roodof geçmişini de sil");
            Button remove = new Button(); remove.Text = T("Uninstall", "Kaldır"); remove.AutoSize = true;
            remove.DialogResult = DialogResult.OK;
            Button cancel = new Button(); cancel.Text = T("Cancel", "Vazgeç"); cancel.AutoSize = true;
            cancel.DialogResult = DialogResult.Cancel;
            FlowLayoutPanel buttons = new FlowLayoutPanel();
            buttons.FlowDirection = FlowDirection.RightToLeft; buttons.AutoSize = true; buttons.Dock = DockStyle.Fill;
            buttons.Margin = new Padding(0); buttons.Controls.Add(cancel); buttons.Controls.Add(remove);
            form.Controls.Add(Stack(message, history, buttons));
            form.AcceptButton = cancel; form.CancelButton = cancel;
            bool accepted = form.ShowDialog() == DialogResult.OK;
            removeHistory = accepted && history.Checked;
            return accepted;
        }
    }

    private static int UninstallRun(string[] args, bool quiet) {
        int parent;
        if (args.Length > 1 && int.TryParse(args[1], NumberStyles.None, CultureInfo.InvariantCulture, out parent)) {
            try { using (Process process = Process.GetProcessById(parent)) process.WaitForExit(15000); } catch (ArgumentException) { }
        }
        try {
            return WithInstallLock(delegate {
            bool removeHistory = false;
            if (!quiet && !Confirm(out removeHistory)) return 2;
            return WithWindow(T("Uninstalling Roodof…", "Roodof kaldırılıyor…"), quiet, delegate(Window window) {
                if (window != null) window.Fraction(0.2);
                if (UpdateRunning()) throw new IOException(T("Roodof is installing an update. Try again when it finishes.",
                    "Roodof bir güncelleme kuruyor. Bittiğinde yeniden deneyin."));
                if (Directory.Exists(Program)) {
                    string old = MoveAside(window, quiet);
                    if (old == null) return 2;
                    RemoveTree(old);
                }
                CleanLeftovers();
                if (window != null) window.Fraction(0.7);
                foreach (string link in new string[] { StartLink, DesktopLink })
                    if (File.Exists(link)) File.Delete(link);
                Registry.CurrentUser.DeleteSubKeyTree(UninstallKey, false);
                // Electron registers its notification activator under this fixed CLSID.
                Registry.CurrentUser.DeleteSubKeyTree(@"Software\Classes\CLSID\{" + ToastClsid.ToString().ToUpperInvariant() + "}", false);
                for (int attempt = 0; attempt < 20 && File.Exists(Uninstaller); attempt++) {
                    try { File.Delete(Uninstaller); } catch (Exception) { Thread.Sleep(500); }
                }
                if (removeHistory) {
                    RemoveTree(History);
                    // Private recovery backups from in-app updates hold history too.
                    if (Directory.Exists(Container))
                        foreach (string folder in Directory.GetDirectories(Container, ".pler-update-*")) RemoveTree(folder);
                }
                if (Directory.Exists(Container) && Directory.GetFileSystemEntries(Container).Length == 0) Directory.Delete(Container);
                if (window != null) window.Fraction(1);
                return 0;
            });
            });
        } finally {
            // Remove this temporary copy once it has exited.
            string self = Assembly.GetExecutingAssembly().Location;
            if (SamePath(Path.GetDirectoryName(self), Path.GetTempPath())) {
                string script = "Wait-Process -Id " + Process.GetCurrentProcess().Id.ToString(CultureInfo.InvariantCulture) +
                    " -ErrorAction SilentlyContinue; Remove-Item -LiteralPath '" + self.Replace("'", "''") + "' -Force";
                string powershell = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), @"WindowsPowerShell\v1.0\powershell.exe");
                ProcessStartInfo info = new ProcessStartInfo(powershell, "-NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand " +
                    Convert.ToBase64String(Encoding.Unicode.GetBytes(script)));
                info.UseShellExecute = false; info.CreateNoWindow = true;
                try { Process.Start(info).Dispose(); } catch (Exception) { }
            }
        }
    }
}
