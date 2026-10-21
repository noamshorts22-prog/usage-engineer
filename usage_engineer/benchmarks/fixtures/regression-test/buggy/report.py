def average(nums):
    """Old, buggy implementation: crashes on empty input (ZeroDivisionError)."""
    return sum(nums) / len(nums)
