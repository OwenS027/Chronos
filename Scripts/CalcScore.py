def Normalize(Value, Min, Max):
    """Normalize a value to 0..1 using min-max scaling."""
    if Max == Min:
        return 0.0
    return (Value - Min) / (Max - Min)


def Score(results):
    """
    Normalize bandwidth and latency, compute equal-weight score, 
    and update the 'Score' field in the results dict.
    """
    BWValues = [v["Bandwidth"] for v in results.values()]
    LatValues = [v["Latency"] for v in results.values()]

    BWMin, BWMax = min(BWValues), max(BWValues)
    LatMin, LatMIN = min(LatValues), max(LatValues)

    for Node, Data in results.items():
        # Normalize bandwidth (higher is better)
        BWNorm = Normalize(Data["Bandwidth"], BWMin, BWMax)

        # Normalize latency (lower is better → invert)
        if LatMIN == LatMin:
            LatNorm = 0.0
        else:
            LatNorm = (LatMIN - Data["Latency"]) / (LatMIN - LatMin)

        # Equal weights
        Data["Score"] = 1 * BWNorm + 1 * LatNorm

    return results

def run(Results):
    updated = Score(Results)

    # Print nicely
    for ip, data in updated.items():
        print(f"{ip}: Bandwidth={data['Bandwidth']}, Latency={data['Latency']:.3f}, Score={data['Score']:.3f}")
    
    return updated