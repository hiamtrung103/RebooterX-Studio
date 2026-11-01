using System;
using System.IO;
class ConsoleFixture {
    static void Main(string[] args) {
        string folder = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "optimizerNXT-logs");
        Directory.CreateDirectory(folder);
        string file = Path.Combine(folder, "fixture.log");
        string[] messages = {"Verified 1/1 YAML files.", "Executing step: Harmless fixture", "Finished executing YAML stage: Fixture", "Exiting."};
        foreach (string message in messages) {
            string line = "[2026-11-01 12:00:00] [INFO]: " + message;
            Console.WriteLine(line);
            File.AppendAllText(file, line + Environment.NewLine);
        }
        Console.ReadKey();
    }
}
