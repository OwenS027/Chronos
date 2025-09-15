from kubernetes import client, config, watch
import traceback
import json
import os

import FetchIPs
import Bandwidth
import Latency
import CalcScore


def SchedulePod(Namespace, PodName, AvailableNodes, PodLabel):

    if os.path.exists("Data.json"):
        with open("Data.json", "r") as f:
            Data = json.load(f)
        print("Found existing Data!", flush=True)
    
        if Data[PodLabel] != None:
            BestIP = max(Data[PodLabel], key=lambda Node: Data[PodLabel][Node]['Score'])
    else:
        print("No existing Data found!", flush=True)
        IPs = FetchIPs.run(Namespace, PodName, PodLabel)

        Results = {}
        for PHost in AvailableNodes:
            AvgLatency = []
            Results[str(PHost)] = {}       
            Results[str(PHost)]["Bandwidth"] = Bandwidth.run(PHost)
            for DHosts in IPs:
                AvgLatency += [Latency.run(PHost, DHosts.split("/")[2])]

            print(AvgLatency, flush=True)

            Results[str(PHost)]["Latency"] = sum(AvgLatency) / len(AvgLatency)
        
        Results = CalcScore.run(Results)
        if os.path.exists("Data.json"):
            with open("Data.json", "r") as f:
                Data = json.load(f)
        else:
            Data = {}
        Data[PodLabel] = Results
        with open("Data.json", "w") as f:
            json.dump(Data, f, indent=4)
    
        BestIP = max(Results, key=lambda Node: Results[Node]['Score'])
    return BestIP

def main():
    AvailableNodes = ["192.168.0.109", "192.168.0.72", "192.168.0.59"]

    config.load_incluster_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    for event in w.stream(v1.list_pod_for_all_namespaces):
        pod = event["object"]

        if (
            pod.spec.scheduler_name == "chronos"
            and pod.spec.node_name is None
            and event["type"] in ["ADDED", "MODIFIED"]
        ):
            Namespace = pod.metadata.namespace
            PodName = pod.metadata.name

            try:
                TargetIP = SchedulePod(Namespace, PodName, AvailableNodes, pod.metadata.labels["app"])
                for node in v1.list_node().items:
                    for addr in node.status.addresses:
                        if addr.address == TargetIP:
                            TargetNode = node.metadata.name
                binding = client.V1Binding(
                    metadata=client.V1ObjectMeta(name=PodName, namespace=Namespace),
                    target=client.V1ObjectReference(
                        api_version="v1",
                        kind="Node",
                        name=TargetNode,
                    ),
                )
                v1.create_namespaced_binding(namespace=Namespace, body=binding,  _preload_content=False)
                print(f"Bound {PodName} -> {TargetNode}", flush=True)

            except Exception as e:
                print(f"Failed to schedule {PodName}: {e}", flush=True)
                traceback.print_exc()  


if __name__ == "__main__":
    print("Script Started!", flush=True)
    main()