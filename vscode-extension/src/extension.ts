import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

let outputChannel: vscode.OutputChannel;
let diagnosticCollection: vscode.DiagnosticCollection;

export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel('ShenCha');
    diagnosticCollection = vscode.languages.createDiagnosticCollection('shencha');

    context.subscriptions.push(
        vscode.commands.registerCommand('shencha.audit', auditCurrentFile),
        vscode.commands.registerCommand('shencha.auditProject', auditProject),
        vscode.commands.registerCommand('shencha.showReport', showReport),
        diagnosticCollection
    );

    const config = vscode.workspace.getConfiguration('shencha');
    if (config.get('autoAudit')) {
        vscode.workspace.onDidSaveTextDocument(doc => auditFile(doc.uri));
    }

    outputChannel.appendLine('ShenCha activated');
}

async function auditCurrentFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No file open');
        return;
    }
    await auditFile(editor.document.uri);
}

async function auditFile(uri: vscode.Uri) {
    const config = vscode.workspace.getConfiguration('shencha');
    const lang = config.get<string>('language') || 'en';

    outputChannel.appendLine(`Auditing: ${uri.fsPath}`);

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'ShenCha: Auditing...',
        cancellable: false
    }, async () => {
        try {
            const { stdout } = await execAsync(`shencha audit "${uri.fsPath}" --format json --lang ${lang}`);
            const result = JSON.parse(stdout);
            showDiagnostics(uri, result.issues || []);
            vscode.window.showInformationMessage(`ShenCha: Score ${result.score}/100, ${result.issues?.length || 0} issues`);
        } catch (e: any) {
            outputChannel.appendLine(`Error: ${e.message}`);
            vscode.window.showErrorMessage('ShenCha audit failed. Check output for details.');
        }
    });
}

async function auditProject() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showWarningMessage('No workspace open');
        return;
    }

    const config = vscode.workspace.getConfiguration('shencha');
    const lang = config.get<string>('language') || 'en';

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'ShenCha: Auditing project...',
        cancellable: false
    }, async () => {
        try {
            const { stdout } = await execAsync(`shencha audit "${workspaceFolder.uri.fsPath}" --format html --lang ${lang}`);
            outputChannel.appendLine(stdout);
            vscode.window.showInformationMessage('ShenCha: Report generated', 'Open Report').then(sel => {
                if (sel === 'Open Report') showReport();
            });
        } catch (e: any) {
            outputChannel.appendLine(`Error: ${e.message}`);
            vscode.window.showErrorMessage('ShenCha audit failed');
        }
    });
}

async function showReport() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) return;

    const reportDir = vscode.Uri.joinPath(workspaceFolder.uri, '.shencha', 'reports');
    try {
        const files = await vscode.workspace.fs.readDirectory(reportDir);
        const htmlFiles = files.filter(([name]) => name.endsWith('.html')).sort().reverse();
        if (htmlFiles.length > 0) {
            const reportUri = vscode.Uri.joinPath(reportDir, htmlFiles[0][0]);
            vscode.env.openExternal(reportUri);
        } else {
            vscode.window.showWarningMessage('No reports found. Run audit first.');
        }
    } catch {
        vscode.window.showWarningMessage('No reports found');
    }
}

function showDiagnostics(uri: vscode.Uri, issues: any[]) {
    const diagnostics: vscode.Diagnostic[] = issues.map(issue => {
        const line = Math.max(0, (issue.line || 1) - 1);
        const range = new vscode.Range(line, 0, line, 1000);
        const severity = {
            critical: vscode.DiagnosticSeverity.Error,
            high: vscode.DiagnosticSeverity.Error,
            medium: vscode.DiagnosticSeverity.Warning,
            low: vscode.DiagnosticSeverity.Information
        }[issue.severity as string] || vscode.DiagnosticSeverity.Warning;

        const diag = new vscode.Diagnostic(range, issue.message, severity);
        diag.source = 'ShenCha';
        diag.code = issue.category;
        return diag;
    });

    diagnosticCollection.set(uri, diagnostics);
}

export function deactivate() {
    diagnosticCollection?.dispose();
}
