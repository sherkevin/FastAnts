def tower_of_hanoi(n, source, target, auxiliary):
    """
    Solve the Tower of Hanoi problem recursively.
    
    Args:
        n (int): Number of disks
        source (str): Name of the source peg
        target (str): Name of the target peg
        auxiliary (str): Name of the auxiliary peg
    
    Returns:
        list: List of moves to solve the puzzle
    """
    moves = []
    
    if n == 1:
        moves.append(f"Move disk 1 from {source} to {target}")
        return moves
    
    # Move n-1 disks from source to auxiliary
    moves.extend(tower_of_hanoi(n - 1, source, auxiliary, target))
    
    # Move the largest disk from source to target
    moves.append(f"Move disk {n} from {source} to {target}")
    
    # Move n-1 disks from auxiliary to target
    moves.extend(tower_of_hanoi(n - 1, auxiliary, target, source))
    
    return moves


def print_hanoi_solution(n):
    """
    Print the solution for Tower of Hanoi with n disks.
    
    Args:
        n (int): Number of disks
    """
    if n <= 0:
        print("Number of disks must be positive!")
        return
    
    print(f"Solving Tower of Hanoi with {n} disks:")
    print("=" * 50)
    
    moves = tower_of_hanoi(n, "A", "C", "B")
    
    for i, move in enumerate(moves, 1):
        print(f"Step {i}: {move}")
    
    print("=" * 50)
    print(f"Total moves: {len(moves)}")
    print(f"Minimum possible moves: {2**n - 1}")


def visualize_hanoi_state(n, moves_to_show=None):
    """
    Visualize the Tower of Hanoi state at different steps.
    
    Args:
        n (int): Number of disks
        moves_to_show (list): List of move numbers to visualize (None for all)
    """
    def print_pegs(pegs):
        max_height = max(len(peg) for peg in pegs.values())
        
        for level in range(max_height - 1, -1, -1):
            line = ""
            for peg_name in ["A", "B", "C"]:
                if level < len(pegs[peg_name]):
                    disk_size = pegs[peg_name][level]
                    disk = "=" * disk_size
                    line += f"  {disk:^{2*n+1}}  "
                else:
                    line += f"  {'|':^{2*n+1}}  "
            print(line)
        
        print("  " + "-" * (2*n+1) + "   " + "-" * (2*n+1) + "   " + "-" * (2*n+1))
        print("     A         B         C")
        print()
    
    # Initialize pegs
    pegs = {
        "A": list(range(n, 0, -1)),
        "B": [],
        "C": []
    }
    
    print("Initial state:")
    print_pegs(pegs)
    
    moves = tower_of_hanoi(n, "A", "C", "B")
    
    if moves_to_show is None:
        moves_to_show = list(range(0, len(moves) + 1, max(1, len(moves) // 5)))
    
    for i, move in enumerate(moves, 1):
        # Parse the move
        parts = move.split()
        disk = int(parts[1])
        from_peg = parts[3]
        to_peg = parts[5]
        
        # Make the move
        pegs[from_peg].pop()
        pegs[to_peg].append(disk)
        
        # Show state if requested
        if i in moves_to_show:
            print(f"After move {i}: {move}")
            print_pegs(pegs)


if __name__ == "__main__":
    # Example usage
    num_disks = 3
    
    print("Tower of Hanoi Solution")
    print("=" * 50)
    print_hanoi_solution(num_disks)
    
    print("\nVisualization of key states:")
    print("=" * 50)
    visualize_hanoi_state(num_disks, [0, 3, 5, 7])
    
    # Interactive mode
    print("\n" + "=" * 50)
    try:
        user_input = input("Enter number of disks to solve (or 'q' to quit): ")
        if user_input.lower() != 'q':
            n = int(user_input)
            if 1 <= n <= 8:  # Limit to reasonable size
                print_hanoi_solution(n)
            else:
                print("Please enter a number between 1 and 8")
    except ValueError:
        print("Invalid input. Please enter a number.")
