"""
FastBox Delivery System - Logistics Simulator
==============================================
Simulates one day of delivery operations for the fictional FastBox company.

How it works:
1. Reads a JSON input file containing warehouses, agents, and packages.
2. Assigns each package to the nearest agent (by Euclidean distance from
   the agent's starting position to the package's warehouse).
3. Simulates deliveries: each agent travels from their current position
   to the warehouse, picks up the package, then delivers it to the destination.
4. Generates a report with per-agent statistics and identifies the best agent.
5. Saves the report to report.json.

Usage:
    python delivery_system.py                          # uses base_case.json
    python delivery_system.py base_case.json           # explicit file
    python delivery_system.py "Python Assignment(Delivery System Test Cases)/test_case_1.json"
"""

import json
import math
import sys
import os
import random
import csv


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def euclidean_distance(point1, point2):
    """
    Calculate the Euclidean distance between two 2D points.

    Args:
        point1: A list/tuple [x, y] representing the first point.
        point2: A list/tuple [x, y] representing the second point.

    Returns:
        Float distance between the two points.

    Example:
        >>> euclidean_distance([0, 0], [3, 4])
        5.0
    """
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    return math.sqrt(dx * dx + dy * dy)


# =============================================================================
# JSON PARSING - Handles both input formats
# =============================================================================

def parse_input(filepath):
    """
    Read and parse the JSON input file, normalizing it into a unified format.

    Supports two JSON formats:

    Format A (base_case.json):
        - warehouses/agents are arrays of {"id": ..., "location": [x, y]}
        - packages use "warehouse_id" as the key

    Format B (test_case_1.json through test_case_10.json):
        - warehouses/agents are dicts {"W1": [x, y], "A1": [x, y]}
        - packages use "warehouse" as the key

    Args:
        filepath: Path to the JSON input file.

    Returns:
        A tuple of (warehouses, agents, packages) where:
        - warehouses: dict  {warehouse_id: [x, y]}
        - agents:     dict  {agent_id: [x, y]}
        - packages:   list  [{"id": str, "warehouse_id": str, "destination": [x, y]}, ...]
    """
    # Read the JSON file
    with open(filepath, 'r') as file:
        data = json.load(file)

    # --- Parse warehouses ---
    raw_warehouses = data["warehouses"]

    if isinstance(raw_warehouses, list):
        # Format A: list of {"id": "W1", "location": [x, y]}
        warehouses = {}
        for w in raw_warehouses:
            warehouses[w["id"]] = w["location"]
    elif isinstance(raw_warehouses, dict):
        # Format B: {"W1": [x, y], "W2": [x, y]}
        warehouses = raw_warehouses
    else:
        raise ValueError(f"Unexpected warehouses format: {type(raw_warehouses)}")

    # --- Parse agents ---
    raw_agents = data["agents"]

    if isinstance(raw_agents, list):
        # Format A: list of {"id": "A1", "location": [x, y]}
        agents = {}
        for a in raw_agents:
            agents[a["id"]] = a["location"]
    elif isinstance(raw_agents, dict):
        # Format B: {"A1": [x, y], "A2": [x, y]}
        agents = raw_agents
    else:
        raise ValueError(f"Unexpected agents format: {type(raw_agents)}")

    # --- Parse packages ---
    # Normalize the warehouse key: "warehouse_id" (Format A) or "warehouse" (Format B)
    packages = []
    for pkg in data["packages"]:
        warehouse_id = pkg.get("warehouse_id") or pkg.get("warehouse")
        packages.append({
            "id": pkg["id"],
            "warehouse_id": warehouse_id,
            "destination": pkg["destination"]
        })

    print(f"  Loaded {len(warehouses)} warehouses, {len(agents)} agents, {len(packages)} packages")
    return warehouses, agents, packages


# =============================================================================
# PACKAGE ASSIGNMENT - Nearest agent to each package's warehouse
# =============================================================================

def assign_packages(agents, warehouses, packages):
    """
    Assign each package to the nearest agent based on Euclidean distance
    from the agent's STARTING position to the package's warehouse location.

    This uses static assignment - every package is assigned based on the
    agent's original position, not their updated position after deliveries.

    Args:
        agents:     dict {agent_id: [x, y]}
        warehouses: dict {warehouse_id: [x, y]}
        packages:   list of package dicts

    Returns:
        A dict {agent_id: [list of assigned package dicts]}
        Every agent appears in the dict (possibly with an empty list).
    """
    # Initialize assignments - every agent gets an empty list
    assignments = {agent_id: [] for agent_id in agents}

    for package in packages:
        warehouse_location = warehouses[package["warehouse_id"]]

        # Find the nearest agent to this package's warehouse
        nearest_agent = None
        nearest_distance = float('inf')

        for agent_id, agent_location in agents.items():
            dist = euclidean_distance(agent_location, warehouse_location)

            # Use strict less-than for tie-breaking:
            # first agent encountered (alphabetical by dict order) wins ties
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_agent = agent_id

        # Assign the package to the nearest agent
        assignments[nearest_agent].append(package)
        print(f"  {package['id']} --> {nearest_agent} "
              f"(warehouse {package['warehouse_id']} at {warehouse_location}, "
              f"agent distance: {nearest_distance:.2f})")

    return assignments


# =============================================================================
# DELIVERY SIMULATION - Sequential delivery with position tracking
# =============================================================================

def simulate_deliveries(agents, warehouses, assignments):
    """
    Simulate the delivery process for each agent.

    For each agent, process their assigned packages in order:
      1. Travel from current position to the package's warehouse (pick up).
      2. Travel from the warehouse to the package's destination (deliver).
      3. Update the agent's current position to the destination.

    This means delivery ORDER matters - the agent's position accumulates
    across multiple deliveries within the day.

    Args:
        agents:      dict {agent_id: [x, y]} - starting positions
        warehouses:  dict {warehouse_id: [x, y]}
        assignments: dict {agent_id: [list of package dicts]}

    Returns:
        A dict {agent_id: {"packages_delivered": int, "total_distance": float,
                           "delivery_log": [list of delivery details]}}
    """
    results = {}

    for agent_id in agents:
        assigned_packages = assignments[agent_id]
        total_distance = 0.0
        current_position = list(agents[agent_id])  # copy the starting position
        delivery_log = []

        print(f"\n  Agent {agent_id} starting at {current_position} "
              f"- {len(assigned_packages)} package(s) to deliver")

        for package in assigned_packages:
            warehouse_location = warehouses[package["warehouse_id"]]
            destination = package["destination"]

            # Leg 1: Travel to warehouse to pick up the package
            dist_to_warehouse = euclidean_distance(current_position, warehouse_location)

            # Leg 2: Travel from warehouse to destination to deliver
            dist_to_destination = euclidean_distance(warehouse_location, destination)

            leg_distance = dist_to_warehouse + dist_to_destination
            total_distance += leg_distance

            # Log this delivery
            delivery_log.append({
                "package_id": package["id"],
                "from": list(current_position),
                "warehouse": list(warehouse_location),
                "destination": list(destination),
                "dist_to_warehouse": round(dist_to_warehouse, 2),
                "dist_to_destination": round(dist_to_destination, 2),
                "leg_total": round(leg_distance, 2)
            })

            print(f"    {package['id']}: {current_position} --> "
                  f"W({warehouse_location}) [{dist_to_warehouse:.2f}] --> "
                  f"D({destination}) [{dist_to_destination:.2f}]  "
                  f"= {leg_distance:.2f}")

            # Update agent's current position to the delivery destination
            current_position = list(destination)

        results[agent_id] = {
            "packages_delivered": len(assigned_packages),
            "total_distance": total_distance,
            "delivery_log": delivery_log
        }

        print(f"  Agent {agent_id} total distance: {total_distance:.2f}")

    return results


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(agents, results):
    """
    Generate the final delivery report with per-agent statistics
    and determine the best (most efficient) agent.

    Efficiency = total_distance / packages_delivered
    (lower is better - less distance per package = more efficient)

    Args:
        agents:  dict {agent_id: [x, y]} - for ordering
        results: dict from simulate_deliveries()

    Returns:
        A dict suitable for writing to report.json
    """
    report = {}
    best_agent = None
    best_efficiency = float('inf')

    for agent_id in agents:
        agent_result = results[agent_id]
        packages_delivered = agent_result["packages_delivered"]
        total_distance = round(agent_result["total_distance"], 2)

        # Calculate efficiency (distance per package)
        # Handle zero-package edge case to avoid division by zero
        if packages_delivered > 0:
            efficiency = round(total_distance / packages_delivered, 2)
        else:
            efficiency = 0.0

        report[agent_id] = {
            "packages_delivered": packages_delivered,
            "total_distance": total_distance,
            "efficiency": efficiency
        }

        # Track the best agent (lowest efficiency = most efficient)
        # Only consider agents who actually delivered packages
        if packages_delivered > 0 and efficiency < best_efficiency:
            best_efficiency = efficiency
            best_agent = agent_id

    # Add the best agent to the report
    report["best_agent"] = best_agent

    return report


# =============================================================================
# REPORT SAVING
# =============================================================================

def save_report(report, filepath="report.json"):
    """
    Save the delivery report to a JSON file.

    Args:
        report:   The report dictionary to save.
        filepath: Output file path (default: report.json).
    """
    with open(filepath, 'w') as file:
        json.dump(report, file, indent=4)

    print(f"\n  Report saved to: {os.path.abspath(filepath)}")


# =============================================================================
# BONUS: Random Delivery Delays
# =============================================================================

def add_random_delays(results):
    """
    Bonus Feature: Add random delivery delays (in minutes) to each delivery.

    Simulates real-world conditions like traffic, weather, and access issues.
    Delays range from 5 to 45 minutes per delivery.

    Args:
        results: dict from simulate_deliveries() - modified in place.

    Returns:
        The modified results dict with delay info added.
    """
    print("\n--- Bonus: Random Delivery Delays ---")
    random.seed(42)  # Reproducible results for testing

    for agent_id, agent_result in results.items():
        total_delay = 0
        for delivery in agent_result["delivery_log"]:
            delay = random.randint(5, 45)
            delivery["delay_minutes"] = delay
            total_delay += delay

        agent_result["total_delay_minutes"] = total_delay

        if agent_result["packages_delivered"] > 0:
            print(f"  Agent {agent_id}: total delay = {total_delay} minutes "
                  f"(avg {total_delay / agent_result['packages_delivered']:.1f} min/package)")

    return results


# =============================================================================
# BONUS: Export Top Performer to CSV
# =============================================================================

def export_top_performer_csv(report, results, filepath="top_performer.csv"):
    """
    Bonus Feature: Export the top performer's details to a CSV file.

    Args:
        report:   The generated report dict.
        results:  The simulation results dict.
        filepath: Output CSV file path.
    """
    best_agent = report["best_agent"]
    if best_agent is None:
        print("  No top performer to export (no deliveries made).")
        return

    agent_stats = report[best_agent]
    agent_deliveries = results[best_agent]["delivery_log"]

    print(f"\n--- Bonus: Exporting Top Performer ({best_agent}) to CSV ---")

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Header section
        writer.writerow(["Top Performer Report"])
        writer.writerow(["Agent ID", best_agent])
        writer.writerow(["Packages Delivered", agent_stats["packages_delivered"]])
        writer.writerow(["Total Distance", agent_stats["total_distance"]])
        writer.writerow(["Efficiency (dist/pkg)", agent_stats["efficiency"]])
        writer.writerow([])  # blank row

        # Delivery details
        writer.writerow(["Package", "From", "Warehouse", "Destination",
                         "Dist to Warehouse", "Dist to Destination", "Leg Total"])
        for d in agent_deliveries:
            writer.writerow([
                d["package_id"],
                str(d["from"]),
                str(d["warehouse"]),
                str(d["destination"]),
                d["dist_to_warehouse"],
                d["dist_to_destination"],
                d["leg_total"]
            ])

    print(f"  Saved to: {os.path.abspath(filepath)}")


# =============================================================================
# MAIN - Orchestrate everything
# =============================================================================

def main():
    """
    Main function - orchestrates the entire delivery simulation.

    Usage:
        python delivery_system.py [input_file.json]

    If no input file is specified, defaults to 'base_case.json'.
    """
    # Determine input file from command-line argument or default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "base_case.json"

    print("=" * 60)
    print("  FastBox Delivery System - Daily Operations Simulator")
    print("=" * 60)

    # --- Step 1: Parse input data ---
    print(f"\n[1] Reading input from: {input_file}")
    try:
        warehouses, agents, packages = parse_input(input_file)
    except FileNotFoundError:
        print(f"  ERROR: File '{input_file}' not found!")
        print(f"  Please provide a valid JSON file path.")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"  ERROR: Failed to parse '{input_file}': {e}")
        sys.exit(1)

    # --- Step 2: Assign packages to nearest agents ---
    print(f"\n[2] Assigning packages to nearest agents...")
    assignments = assign_packages(agents, warehouses, packages)

    # Print assignment summary
    print(f"\n  Assignment Summary:")
    for agent_id, pkgs in assignments.items():
        pkg_ids = [p["id"] for p in pkgs]
        print(f"    {agent_id}: {pkg_ids if pkg_ids else '(no packages)'}")

    # --- Step 3: Simulate deliveries ---
    print(f"\n[3] Simulating deliveries...")
    results = simulate_deliveries(agents, warehouses, assignments)

    # --- Step 4: Add bonus random delays ---
    results = add_random_delays(results)

    # --- Step 5: Generate report ---
    print(f"\n[4] Generating report...")
    report = generate_report(agents, results)

    # Print report preview
    print(f"\n  Report Preview:")
    for key, value in report.items():
        if key == "best_agent":
            print(f"    Best Agent: {value}")
        else:
            print(f"    {key}: delivered={value['packages_delivered']}, "
                  f"distance={value['total_distance']}, "
                  f"efficiency={value['efficiency']}")

    # --- Step 6: Save report ---
    print(f"\n[5] Saving report...")
    save_report(report)

    # --- Step 7: Export top performer CSV (bonus) ---
    export_top_performer_csv(report, results)

    # --- Validation check ---
    total_delivered = sum(
        report[a]["packages_delivered"] for a in agents
    )
    print(f"\n{'=' * 60}")
    print(f"  Validation: {total_delivered}/{len(packages)} packages delivered")
    if total_delivered == len(packages):
        print(f"  [OK] All packages accounted for!")
    else:
        print(f"  [FAIL] WARNING: Package count mismatch!")
    print(f"{'=' * 60}")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
