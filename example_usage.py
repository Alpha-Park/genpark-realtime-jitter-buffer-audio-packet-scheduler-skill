import json
from client import RealtimeJitterBufferAudioPacketScheduler

def main():
    scheduler = RealtimeJitterBufferAudioPacketScheduler(target_latency_ms=40)
    # Simulate out-of-order packet arrival: 100, 102, 101
    scheduler.push_packet({"seq": 100, "timestamp": 1000, "payload_bytes": "pcm_chunk_0"})
    scheduler.push_packet({"seq": 102, "timestamp": 1040, "payload_bytes": "pcm_chunk_2"})
    scheduler.push_packet({"seq": 101, "timestamp": 1020, "payload_bytes": "pcm_chunk_1"})

    f1 = scheduler.pop_next_playable_frame()
    f2 = scheduler.pop_next_playable_frame()
    f3 = scheduler.pop_next_playable_frame()

    print("Frame 1 (Seq):", f1["seq"])
    print("Frame 2 (Seq):", f2["seq"])
    print("Frame 3 (Seq):", f3["seq"])

    assert f1["seq"] == 100
    assert f2["seq"] == 101
    assert f3["seq"] == 102
    print("Jitter buffer packet scheduler verification: PASS")

if __name__ == "__main__":
    main()
