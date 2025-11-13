import matplotlib.pyplot as plt

def carbon_emission_calculator():
    print("=== 🌱 Electricity & Carbon Emission Savings Calculator ===\n")
    
    months = []
    units_list = []
    co2_list = []
    renewable_co2_list = []
    cost_list = []
    renewable_cost_list = []

    emission_factor = 0.85  # kg CO₂ per kWh (average grid electricity)
    renewable_factor = 0.05  # kg CO₂ per kWh (renewables like solar/wind)
    cost_per_unit = 7.0  # average electricity cost (₹7 or $0.08 per kWh)
    renewable_cost_per_unit = 2.5  # effective cost with solar (after setup savings)

    try:
        n = int(input("Enter number of months you want to track: "))
        for i in range(n):
            month = input(f"\nEnter month name ({i+1}): ")
            units = float(input(f"Enter electricity units consumed in {month} (kWh): "))
            
            # Calculate emissions & cost
            co2 = units * emission_factor
            renewable_co2 = units * renewable_factor
            cost = units * cost_per_unit
            renewable_cost = units * renewable_cost_per_unit

            months.append(month)
            units_list.append(units)
            co2_list.append(co2)
            renewable_co2_list.append(renewable_co2)
            cost_list.append(cost)
            renewable_cost_list.append(renewable_cost)

        # Calculate total savings
        total_co2_saving = sum(co2_list) - sum(renewable_co2_list)
        total_cost_saving = sum(cost_list) - sum(renewable_cost_list)

        # Display Summary
        print("\n=== Summary ===")
        for i in range(n):
            print(f"{months[i]}: {units_list[i]} kWh → {co2_list[i]:.2f} kg CO₂ → ₹{cost_list[i]:.2f}")
        print("\n--- If using renewable energy ---")
        for i in range(n):
            print(f"{months[i]}: {units_list[i]} kWh → {renewable_co2_list[i]:.2f} kg CO₂ → ₹{renewable_cost_list[i]:.2f}")
        
        print("\n=== 🌍 Estimated Savings ===")
        print(f"CO₂ Reduction: {total_co2_saving:.2f} kg per year")
        print(f"Cost Savings: ₹{total_cost_saving:.2f} per year")

        # Plot comparison chart
        plt.figure(figsize=(9, 6))
        x = range(len(months))
        
        plt.bar(x, co2_list, width=0.4, label='Normal CO₂ (kg)', color='red')
        plt.bar([i + 0.4 for i in x], renewable_co2_list, width=0.4, label='Renewable CO₂ (kg)', color='green')
        plt.xticks([i + 0.2 for i in x], months)
        
        plt.title("CO₂ Emission Comparison: Grid vs Renewable Energy")
        plt.xlabel("Month")
        plt.ylabel("CO₂ Emitted (kg)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.show()

    except ValueError:
        print("❌ Invalid input. Please enter numeric values.")

if __name__ == "__main__":
    carbon_emission_calculator()
