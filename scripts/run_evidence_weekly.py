"""W121.1: weekly evidence look entrypoint (cron + box task). Thin wrapper over decision_trees.evidence.weekly.main."""
import sys

from prediction_market_bot.decision_trees.evidence.weekly import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
