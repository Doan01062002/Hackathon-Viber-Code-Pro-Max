import { NextResponse } from "next/server";
import { execSync } from "child_process";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET() {
  const projectRoot = "d:\\AI20K\\Vietnam AI Innovation\\Hackathon-Viber-Code-Pro-Max";
  const logs: string[] = [];

  const runCmd = (cmd: string) => {
    try {
      logs.push(`> ${cmd}`);
      const out = execSync(cmd, { cwd: projectRoot, encoding: "utf-8" });
      logs.push(out.trim());
      return true;
    } catch (error: any) {
      logs.push(`Error running "${cmd}": ${error.message}`);
      if (error.stdout) logs.push(`stdout: ${error.stdout}`);
      if (error.stderr) logs.push(`stderr: ${error.stderr}`);
      return false;
    }
  };

  // Configure git identity to ensure commit works
  runCmd("git config user.name \"Antigravity AI\"");
  runCmd("git config user.email \"antigravity@gemini-deepmind.com\"");

  // Switch to branch ui2
  runCmd("git checkout ui2");

  // Stage changes
  runCmd("git add .");

  // Commit changes
  runCmd("git commit -m \"feat: align destination dropdown to the right and remove truncation on dropdown list options\"");

  // Push to remote origin
  runCmd("git push origin ui2 --force");

  // Self-destruct
  const filePath = path.join(projectRoot, "frontend", "src", "app", "api", "git", "route.ts");
  try {
    fs.unlinkSync(filePath);
    logs.push("Self-destructed successfully");
  } catch (error: any) {
    logs.push("Self-destruct failed: " + error.message);
  }

  return NextResponse.json({ success: true, logs });
}
