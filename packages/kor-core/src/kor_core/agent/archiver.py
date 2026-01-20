"""
Plan Archiver for Long-Term Memory.

Archives completed plans to build institutional knowledge:
1. Summarizes what was accomplished
2. Extracts patterns and preferences
3. Stores in MemoryDB for future reference
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ArchivedPlan:
    """Represents an archived execution plan."""
    timestamp: str
    user_goal: str
    tasks_completed: int
    tasks_total: int
    summary: str
    insights: List[str]
    duration_seconds: Optional[float] = None

class PlanArchiver:
    """
    Archives completed plans for long-term learning.
    
    Storage: ~/.kor/memory/plans.jsonl
    """
    
    def __init__(self, memory_path: Optional[Path] = None):
        if memory_path is None:
            memory_path = Path.home() / ".kor" / "memory" / "plans.jsonl"
        self.memory_path = memory_path
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
    
    def archive_plan(
        self,
        user_goal: str,
        plan_tasks: List[Dict[str, Any]],
        summary: Optional[str] = None,
        insights: Optional[List[str]] = None
    ) -> ArchivedPlan:
        """
        Archives a completed plan.
        
        Args:
            user_goal: Original user objective
            plan_tasks: List of PlanTask dicts
            summary: Optional execution summary
            insights: Optional learned insights
            
        Returns:
            ArchivedPlan object
        """
        completed = sum(1 for t in plan_tasks if t.get("status") == "completed")
        total = len(plan_tasks)
        
        # Auto-generate summary if not provided
        if not summary:
            task_descriptions = [t["description"] for t in plan_tasks if t.get("status") == "completed"]
            summary = f"Completed {completed}/{total} tasks: " + "; ".join(task_descriptions[:3])
            if len(task_descriptions) > 3:
                summary += f" (+{len(task_descriptions) - 3} more)"
        
        # Auto-extract simple insights
        if not insights:
            insights = []
            # Example: detect tool preferences
            tool_mentions = {}
            for t in plan_tasks:
                desc = t.get("description", "").lower()
                if "pytest" in desc:
                    tool_mentions["pytest"] = tool_mentions.get("pytest", 0) + 1
                if "unittest" in desc:
                    tool_mentions["unittest"] = tool_mentions.get("unittest", 0) + 1
            
            for tool, count in tool_mentions.items():
                if count >= 2:
                    insights.append(f"User frequently uses {tool} for testing")
        
        archived = ArchivedPlan(
            timestamp=datetime.now().isoformat(),
            user_goal=user_goal,
            tasks_completed=completed,
            tasks_total=total,
            summary=summary,
            insights=insights
        )
        
        # Write to JSONL
        self._write_entry(archived)
        logger.info(f"Archived plan: {completed}/{total} tasks for goal: {user_goal[:50]}...")
        
        return archived
    
    def _write_entry(self, archived: ArchivedPlan) -> None:
        """Appends an entry to the JSONL file."""
        entry = {
            "timestamp": archived.timestamp,
            "user_goal": archived.user_goal,
            "tasks_completed": archived.tasks_completed,
            "tasks_total": archived.tasks_total,
            "summary": archived.summary,
            "insights": archived.insights
        }
        
        with open(self.memory_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_recent_insights(self, limit: int = 10) -> List[str]:
        """Retrieves recent insights from archived plans."""
        if not self.memory_path.exists():
            return []
        
        all_insights = []
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        all_insights.extend(entry.get("insights", []))
        except Exception as e:
            logger.warning(f"Failed to read memory: {e}")
            return []
        
        # Return most recent unique insights
        seen = set()
        unique = []
        for insight in reversed(all_insights):
            if insight not in seen:
                seen.add(insight)
                unique.append(insight)
                if len(unique) >= limit:
                    break
        
        return unique
    
    def get_success_rate(self) -> float:
        """Calculates historical task completion rate."""
        if not self.memory_path.exists():
            return 0.0
        
        total_completed = 0
        total_tasks = 0
        
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        total_completed += entry.get("tasks_completed", 0)
                        total_tasks += entry.get("tasks_total", 0)
        except Exception:
            return 0.0
        
        if total_tasks == 0:
            return 0.0
        
        return total_completed / total_tasks
