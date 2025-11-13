def carbon_emission_calculator():
    print("=== Electricity Carbon Emission Calculator ===\n")

    try:
        units = float(input("Enter the number of electricity units consumed (kWh): "))
        if units < 0:
            print("⚠️ Units cannot be negative.")
            return

        # Approximate carbon emission factor (can vary by country/grid source)
        # 1 kWh of electricity = ~0.85 kg of CO₂ (average global estimate)
        emission_factor = 0.85  

        total_co2 = units * emission_factor

        print(f"\nYou consumed {units:.2f} kWh of electricity.")
        print(f"Estimated CO₂ emitted: {total_co2:.2f} kg")

        # Give a simple message based on usage
        if total_co2 < 50:
            print("🌿 Low carbon footprint — great job!")
        elif total_co2 < 200:
            print("⚙️ Moderate usage — consider some energy-saving habits.")
        else:
            print("🔥 High usage — try using renewable energy sources!")

    except ValueError:
        print("❌ Invalid input. Please enter a numeric value for units.")

# Run the calculator
if __name__ == "__main__":
    carbon_emission_calculator()
