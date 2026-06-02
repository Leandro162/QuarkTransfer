using System;
using System.Diagnostics;
using System.IO;
using System.ServiceProcess;

public sealed class QuarkTrackerService : ServiceBase
{
    private const string ServiceTitle = "Quark Tracker Service";
    private Process child;
    private StreamWriter outputLog;
    private StreamWriter errorLog;

    public QuarkTrackerService()
    {
        ServiceName = "QuarkTracker";
        CanStop = true;
        AutoLog = true;
    }

    public static void Main()
    {
        ServiceBase.Run(new QuarkTrackerService());
    }

    protected override void OnStart(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
        string configDir = Path.Combine(root, "config");
        Directory.CreateDirectory(configDir);

        string python = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
            @".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
        );
        string server = Path.Combine(root, "server.py");

        outputLog = new StreamWriter(Path.Combine(configDir, "quark-tracker-service.out.log"), true);
        errorLog = new StreamWriter(Path.Combine(configDir, "quark-tracker-service.err.log"), true);
        outputLog.AutoFlush = true;
        errorLog.AutoFlush = true;

        if (!File.Exists(python))
        {
            throw new FileNotFoundException("Python runtime was not found.", python);
        }
        if (!File.Exists(server))
        {
            throw new FileNotFoundException("server.py was not found.", server);
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = python,
            Arguments = "\"" + server + "\" --host 127.0.0.1 --port 8765",
            WorkingDirectory = root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };

        child = new Process();
        child.StartInfo = startInfo;
        child.OutputDataReceived += delegate(object sender, DataReceivedEventArgs eventArgs)
        {
            if (eventArgs.Data != null) outputLog.WriteLine(DateTime.Now.ToString("s") + " " + eventArgs.Data);
        };
        child.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs eventArgs)
        {
            if (eventArgs.Data != null) errorLog.WriteLine(DateTime.Now.ToString("s") + " " + eventArgs.Data);
        };

        child.Start();
        child.BeginOutputReadLine();
        child.BeginErrorReadLine();
        outputLog.WriteLine(DateTime.Now.ToString("s") + " " + ServiceTitle + " started.");
    }

    protected override void OnStop()
    {
        try
        {
            if (child != null && !child.HasExited)
            {
                child.Kill();
                child.WaitForExit(5000);
            }
            if (outputLog != null) outputLog.WriteLine(DateTime.Now.ToString("s") + " " + ServiceTitle + " stopped.");
        }
        finally
        {
            if (child != null) child.Dispose();
            if (outputLog != null) outputLog.Dispose();
            if (errorLog != null) errorLog.Dispose();
        }
    }
}
