def hanoi(n, source, target, auxiliary):
    """
    Solve the Tower of Hanoi problem recursively.
    
    Args:
        n (int): Number of disks
        source (str): Name of the source peg
        target (str): Name of the target peg
        auxiliary (str): Name of the auxiliary peg
    """
    if n == 1:
        print(f"Move disk 1 from {source} to {target}")
        return
    
    # Move n-1 disks from source to auxiliary using target as auxiliary
    hanoi(n - 1, source, auxiliary, target)
    
    # Move the nth disk from source to target
    print(f"Move disk {n} from {source} to {target}")
    
    # Move n-1 disks from auxiliary to target using source as auxiliary
    hanoi(n - 1, auxiliary, target, source)


def solve_hanoi(num_disks=3):
    """
    Solve the Tower of Hanoi with a specified number of disks.
    
    Args:
        num_disks (int): Number of disks to use (default: 3)
    """
    if num_disks < 1:
        print("Number of disks must be at least 1")
        return
    
    print(f"Solving Tower of Hanoi with {num_disks} disks:")
    print(f"Total moves required: {2**num_disks - 1}")
    print("-" * 40)
    
    hanoi(num_disks, 'A', 'C', 'B')
    print("-" * 40)
    print("Tower of Hanoi solved!")


if __name__ == "__main__":
    # Example usage
    solve_hanoi(3)
    
    # Uncomment to try with different number of disks
    # solve_hanoi(4)
    # solve_hanoi(5)
