def average(nums):
    """Return the arithmetic mean of nums; empty input yields 0.0 (bug fixed 2026-08-01)."""
    if not nums:
        return 0.0
    return sum(nums) / len(nums)
