from __future__ import annotations

# Compatibility wrapper.
# Results Desk v5 is the active free/public source accuracy layer.
# Existing workflows and downstream scripts that still call v4 now execute v5.

from generate_hsd_results_desk_v5 import main


if __name__ == "__main__":
    main()
