def get_ai_suggestion(units, co2):
    """
    Simulated AI suggestion system that gives energy-saving tips
    based on electricity usage and emissions.
    """

    if units <= 50:
        return (
            "🌿 Excellent! Your consumption is very low. "
            "Keep it up by continuing to use efficient LED bulbs and solar charging devices."
        )
    elif units <= 150:
        return (
            "⚙️ Moderate consumption detected. "
            "Consider unplugging idle electronics and using smart power strips to reduce standby losses."
        )
    elif units <= 300:
        return (
            "⚡ Your electricity usage is on the higher side. "
            "Try scheduling high-power tasks (like washing machines) during off-peak hours, "
            "and switch to inverter-based appliances."
        )
    elif units <= 600:
        return (
            "🔥 Heavy usage! You might benefit from a partial solar panel setup to offset your grid use. "
            "Also, monitor your cooling/heating appliances — they’re often major contributors."
        )
    else:
        return (
            "🚨 Very high energy usage detected! "
            "Consider a full renewable energy plan or energy audit to identify waste sources. "
            "Switching to solar or wind power could reduce over 70% of your CO₂ emissions."
        )


def call_genai_suggestion(units, co2):
    """Try to get a dynamic suggestion from the generative AI service.

    Returns the generated text on success, or None on failure / when disabled.
    """
    if not genai_enabled:
        return None

    prompt = (
        f"You are an energy advisor. The user consumed {units:.2f} kWh "
        f"which produced approximately {co2:.2f} kg CO2. "
        "Provide a concise (2-4 sentences) practical suggestion to reduce energy usage, "
        "mention one low-cost action and one longer-term option."
    )

    try:
        # The exact client method and return shape can vary by package version.
        # We try a common call and safely extract text from the response.
        resp = genai.generate_text(model="text-bison-001", input=prompt)

        # resp may expose `.text`, `.output`, or be a dict with `candidates`.
        text = None
        if hasattr(resp, "text"):
            text = resp.text
        elif isinstance(resp, dict):
            # common shapes
            if resp.get("candidates"):
                text = resp["candidates"][0].get("content")
            elif resp.get("output"):
                first = resp["output"][0]
                if isinstance(first, dict):
                    text = first.get("content")

        if text:
            return text.strip()
    except Exception as e:
        print(f"AI suggestion failed: {e}")

    return None


def carbon_emission_calculator():
    print("=== Smart Electricity & CO₂ Emission Advisor ===\n")

    try:
        units = float(input("Enter the number of electricity units consumed (kWh): "))
        if units < 0:
            print("⚠️ Units cannot be negative.")
            return

        # Average CO₂ emission factor per kWh (in kg)
        emission_factor = 0.85
        total_co2 = units * emission_factor

        print(f"\n📊 You consumed {units:.2f} kWh of electricity.")
        print(f"💨 Estimated CO₂ emitted: {total_co2:.2f} kg")

        # AI-like suggestion based on usage
        suggestion = get_ai_suggestion(units, total_co2)
        print("\n🤖 AI Energy Advisor Suggestion:")
        print(suggestion)

    except ValueError:
        print("❌ Invalid input. Please enter a numeric value for units.")


# Run the AI-powered calculator
if __name__ == "__main__":
    carbon_emission_calculator()


