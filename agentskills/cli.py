"""
AgentSkills CLI - Browse, search, and install agent skills.

Commands:
    skill browse          Browse all skills (paginated)
    skill search <query>  Search skills by keyword
    skill get <name>      View skill details
    skill use <name>      Install skill to your project
"""
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

from agentskills.registry import create_default_registry, SkillRegistry


# Initialize
app = typer.Typer(
    name="skill",
    help="🧠 AgentSkills - Browse & install skills from anthropics/skills",
    add_completion=False,
)
console = Console()

# Lazy-loaded registry
_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """Get or create the skill registry."""
    global _registry
    if _registry is None:
        _registry = create_default_registry()
    return _registry


# ============================================
# Browse Command
# ============================================

@app.command()
def browse(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    per_page: int = typer.Option(15, "--limit", "-n", help="Skills per page"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Force refresh from GitHub"),
):
    """
    📚 Browse all available skills (paginated).
    
    Examples:
        skill browse
        skill browse --page 2
        skill browse --limit 30
    """
    registry = get_registry()
    
    if refresh:
        console.print("[dim]Refreshing from GitHub...[/dim]")
        registry.refresh(force=True)
    
    with console.status("[bold green]Loading skills...[/bold green]"):
        result = registry.browse(page=page, per_page=per_page)
    
    if not result.skills:
        console.print("[yellow]No skills found.[/yellow]")
        return
    
    # Build table
    table = Table(
        title=f"🧠 Skills (Page {result.page}/{result.total_pages})",
        caption=f"Total: {result.total} skills",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan bold", no_wrap=True)
    table.add_column("Description", style="white", max_width=50)
    table.add_column("Tags", style="magenta", max_width=15)
    
    start_num = (page - 1) * per_page + 1
    for i, skill in enumerate(result.skills, start=start_num):
        desc = skill.description[:80] + "..." if len(skill.description) > 80 else skill.description
        tags = ", ".join(skill.tags[:3]) if skill.tags else "-"
        table.add_row(str(i), skill.name, desc, tags)
    
    console.print(table)
    
    # Navigation hints
    nav = []
    if result.has_prev:
        nav.append(f"[dim]← skill browse -p {page - 1}[/dim]")
    if result.has_next:
        nav.append(f"[dim]skill browse -p {page + 1} →[/dim]")
    if nav:
        console.print(" | ".join(nav))


# ============================================
# Search Command
# ============================================

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    per_page: int = typer.Option(15, "--limit", "-n", help="Results per page"),
):
    """
    🔍 Search skills by name, description, or tags.
    
    Examples:
        skill search mcp
        skill search "frontend design"
        skill search pdf --page 2
    """
    registry = get_registry()
    
    with console.status(f"[bold green]Searching for '{query}'...[/bold green]"):
        result = registry.search(query, page=page, per_page=per_page)
    
    if not result.skills:
        console.print(f"[yellow]No skills found matching '{query}'[/yellow]")
        return
    
    # Build table
    table = Table(
        title=f"🔍 Search: '{query}'",
        caption=f"Found {result.total} matches",
    )
    table.add_column("Name", style="cyan bold", no_wrap=True)
    table.add_column("Description", style="white", max_width=55)
    table.add_column("Source", style="dim")
    
    for skill in result.skills:
        desc = skill.description[:80] + "..." if len(skill.description) > 80 else skill.description
        table.add_row(skill.name, desc, skill.source)
    
    console.print(table)
    
    # Pagination hints
    if result.total_pages > 1:
        console.print(f"[dim]Page {result.page}/{result.total_pages}[/dim]")


# ============================================
# Get Command (View Details)
# ============================================

@app.command()
def get(
    name: str = typer.Argument(..., help="Skill name"),
    full: bool = typer.Option(False, "--full", "-f", help="Show full SKILL.md content"),
):
    """
    📄 View details of a specific skill.
    
    Examples:
        skill get mcp-builder
        skill get frontend-design --full
    """
    registry = get_registry()
    
    skill = registry.get(name)
    
    if not skill:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        
        # Suggest similar
        result = registry.search(name, per_page=5)
        if result.skills:
            console.print("\n[yellow]Did you mean:[/yellow]")
            for s in result.skills:
                console.print(f"  • {s.name}")
        return
    
    # Header panel
    extras = []
    if skill.has_scripts:
        extras.append("📜 scripts/")
    if skill.has_references:
        extras.append("📚 reference/")
    
    header = (
        f"[bold cyan]{skill.name}[/bold cyan]\n\n"
        f"{skill.description}\n\n"
        f"[dim]Source: {skill.source} | License: {skill.license or 'Apache 2.0'}[/dim]"
    )
    if extras:
        header += f"\n[dim]Includes: {' '.join(extras)}[/dim]"
    
    console.print(Panel(header, title="📄 Skill Details", border_style="cyan"))
    
    # Content preview
    if full:
        console.print("\n[bold]Full SKILL.md:[/bold]")
        console.print(Panel(Markdown(skill.content), border_style="dim"))
    else:
        preview = "\n".join(skill.content.split("\n")[:40])
        console.print("\n[bold]SKILL.md Preview:[/bold]")
        console.print(Panel(Markdown(preview), border_style="dim"))
        console.print(f"[dim]Use --full to see entire SKILL.md[/dim]")
    
    # Usage instructions
    console.print(f"\n[bold green]To install:[/bold green] skill use {skill.name}")


# ============================================
# Use Command (Install)
# ============================================

@app.command()
def use(
    name: str = typer.Argument(..., help="Skill name to install"),
    target: str = typer.Option(".skills", "--target", "-t", help="Target directory"),
):
    """
    ⬇️ Install a skill to your project.
    
    Copies the skill folder to .skills/ (or custom target).
    Then reference the SKILL.md in Claude Code, API, etc.
    
    Examples:
        skill use mcp-builder
        skill use frontend-design --target ./my-skills
    """
    registry = get_registry()
    
    skill = registry.get(name)
    if not skill:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        return
    
    target_path = Path(target)
    
    with console.status(f"[bold green]Installing {name}...[/bold green]"):
        installed_path = registry.install(skill, target_path)
    
    console.print(f"✅ [bold green]Installed '{skill.name}'[/bold green]")
    console.print(f"   Location: {installed_path}")
    
    # List contents
    console.print("\n[bold]Contents:[/bold]")
    for item in sorted(installed_path.rglob("*")):
        if item.is_file():
            rel = item.relative_to(installed_path)
            size = item.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
            console.print(f"  📄 {rel} [dim]({size_str})[/dim]")
    
    console.print("\n[bold]How to use this skill:[/bold]")
    console.print("  [cyan]Claude Code:[/cyan] Just mention it: \"Use the {skill.name} skill...\"")
    console.print("  [cyan]Claude.ai:[/cyan]   Run: skill zip {skill.name}")
    console.print(f"  [cyan]Direct:[/cyan]     Read: {installed_path / 'SKILL.md'}")


# ============================================
# Zip Command (for Claude.ai upload)
# ============================================

@app.command(name="zip")
def zip_skill(
    name: str = typer.Argument(..., help="Skill name to zip"),
    target: str = typer.Option(".skills", "--target", "-t", help="Skills directory"),
    output: str = typer.Option(".", "--output", "-o", help="Output directory for ZIP"),
):
    """
    📦 Create a ZIP of an installed skill for Claude.ai upload.
    
    Claude.ai requires skills to be uploaded as ZIP files.
    This command creates a properly formatted ZIP.
    
    Examples:
        skill zip mcp-builder
        skill zip frontend-design --output ~/Downloads
    """
    import zipfile
    
    skill_path = Path(target) / name
    
    if not skill_path.exists():
        console.print(f"[red]Skill '{name}' not found in {target}/[/red]")
        console.print(f"[dim]Install it first: skill use {name}[/dim]")
        return
    
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    zip_path = output_path / f"{name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in skill_path.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(skill_path.parent)  # Include skill folder name
                zf.write(file, arcname)
    
    console.print(f"📦 [bold green]Created {zip_path}[/bold green]")
    console.print(f"   Size: {zip_path.stat().st_size / 1024:.1f} KB")
    console.print("\n[bold]Upload to Claude.ai:[/bold]")
    console.print("  1. Go to claude.ai/settings/capabilities")
    console.print("  2. Scroll to Skills section")
    console.print("  3. Click 'Upload skill'")
    console.print(f"  4. Select {zip_path.name}")


# ============================================
# Remove Command
# ============================================

@app.command()
def remove(
    name: str = typer.Argument(..., help="Skill name to remove"),
    target: str = typer.Option(".skills", "--target", "-t", help="Skills directory"),
):
    """
    🗑️ Remove an installed skill from your project.
    
    Examples:
        skill remove mcp-builder
        skill remove frontend-design --target ./my-skills
    """
    import shutil
    
    target_path = Path(target) / name
    
    if not target_path.exists():
        console.print(f"[yellow]Skill '{name}' not found in {target}/[/yellow]")
        
        # List what's installed
        parent = Path(target)
        if parent.exists():
            installed = [d.name for d in parent.iterdir() if d.is_dir()]
            if installed:
                console.print("\n[dim]Installed skills:[/dim]")
                for s in installed:
                    console.print(f"  • {s}")
        return
    
    # Confirm and remove
    shutil.rmtree(target_path)
    console.print(f"🗑️ [bold green]Removed '{name}'[/bold green]")


# ============================================
# Stats Command
# ============================================

@app.command()
def stats():
    """
    📊 Show registry statistics.
    """
    registry = get_registry()
    
    with console.status("[bold green]Loading...[/bold green]"):
        registry.refresh()
    
    console.print(Panel(
        f"[bold]Total Skills:[/bold] {registry.total_skills}\n"
        f"[bold]Sources:[/bold] {', '.join(registry.sources)}",
        title="📊 Registry Stats"
    ))


# ============================================
# Main Entry Point
# ============================================

def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
