import numpy as np # type: ignore
import matplotlib.pyplot as plt # type: ignore

def auto_renewable_prediction():
    print("=== 🌞 Predictive Renewable Energy Growth Model ===\n")

    # --- Fixed parameters (can be tuned) ---
    years = 20                      # total years to simulate
    start_people = 50_000           # initial number of renewable users
    total_population = 1_000_000    # total potential adopters
    avg_generation_per_person = 5000  # kWh/year per person
    growth_rate = 0.22              # annual growth rate (22%)

    # --- Time range (monthly intervals for smooth curve) ---
    t = np.linspace(0, years, years * 12 + 1)

    # --- Logistic growth model for adoption ---
    K = total_population
    N0 = start_people
    r = growth_rate
    people_using = K / (1 + ((K - N0) / N0) * np.exp(-r * t))

    # --- Renewable power generation (kWh) ---
    generation = people_using * avg_generation_per_person

    # --- Display summary at 5-year intervals ---
    print("Year | People Using Renewables | Energy Generated (kWh)")
    print("---------------------------------------------------------")
    for i in range(0, len(t), 60):  # every 5 years
        print(f"{int(t[i]):>4} | {int(people_using[i]):>15,} | {generation[i]:>15,.0f}")

    # --- Plot results ---
    plt.figure(figsize=(10, 6))

    plt.plot(t, people_using / 1000, color='green', linewidth=2.5, label='People Using Renewables (×1000)')
    plt.plot(t, generation / 1e6, color='blue', linewidth=2.5, linestyle='--', label='Renewable Energy (Million kWh)')

    plt.title("Predicted Growth of Renewable Adoption & Energy Generation (20 Years)")
    plt.xlabel("Time (Years)")
    plt.ylabel("Value (Scaled)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    auto_renewable_prediction()
