# FastBox Delivery System

A Python-based logistics simulator that models one day of delivery operations for the fictional FastBox company.

## Features

* Reads delivery data from JSON files
* Supports base-case and test-case JSON formats
* Assigns each package to the nearest delivery agent using Euclidean distance
* Simulates sequential package deliveries
* Tracks agent position after each delivery
* Calculates total delivery distance
* Calculates distance-per-package efficiency
* Generates a JSON delivery report
* Validates that all packages are delivered
* Simulates random delivery delays
* Exports the top-performing agent's details to CSV

## Project Structure

```text
Python-Assignment/
├── delivery_system.py
├── base_case.json
├── Python Assignment(Delivery System Test Cases)/
│   ├── test_case_1.json
│   ├── test_case_2.json
│   ├── test_case_3.json
│   ├── test_case_4.json
│   ├── test_case_5.json
│   ├── test_case_6.json
│   ├── test_case_7.json
│   ├── test_case_8.json
│   ├── test_case_9.json
│   └── test_case_10.json
├── report.json
└── top_performer.csv
```

## How to Run

Run the base case:

```bash
python delivery_system.py
```

Run a specific test case:

```bash
python delivery_system.py "Python Assignment(Delivery System Test Cases)/test_case_1.json"
```

## Core Logic

### Package Assignment

Each package is assigned to the nearest agent based on the Euclidean distance between the agent's starting position and the package's warehouse.

### Delivery Simulation

For each assigned package, the agent:

1. Travels from the current position to the warehouse.
2. Picks up the package.
3. Travels from the warehouse to the destination.
4. Updates the current position to the destination.

### Efficiency

```text
Efficiency = Total Distance / Packages Delivered
```

Agents with fewer distance units per delivered package have better distance efficiency.

## Output Files

### report.json

Contains:

* Packages delivered by each agent
* Total distance
* Efficiency
* Best agent

### top_performer.csv

Contains the top performer's:

* Agent ID
* Packages delivered
* Total distance
* Efficiency
* Delivery details

## Bonus Features

### Random Delivery Delays

Each delivery receives a simulated delay between 5 and 45 minutes.

A fixed random seed is used to make the results reproducible.

### CSV Export

The top-performing agent's delivery information is exported to `top_performer.csv`.

## Assumptions

* Package assignment is based on each agent's original starting position.
* After every delivery, the agent's current position becomes that package's destination.
* Packages are processed in the order provided by the input.
* If agents have equal distances to a warehouse, the first agent encountered is selected.
* Agents with zero assigned packages are not considered for best-agent selection.

## Validation

The program performs a final validation by comparing the total number of delivered packages with the number of packages in the input.

Example:

```text
Validation: 5/5 packages delivered
[OK] All packages accounted for!
```

## Technologies

* Python 3
* JSON
* CSV
* Standard Python libraries
* Euclidean distance calculation

## Author

Alfiya Mulani
