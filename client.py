import collections
from typing import Dict, Any, List, Optional

class RealtimeJitterBufferAudioPacketScheduler:
    """
    Maintains an adaptive jitter buffer queue for incoming RTP/WebSocket audio packets.
    Reorders out-of-order packets, handles packet loss concealment (PLC), and regulates playback clock drift.
    """
    def __init__(self, target_latency_ms: int = 60, max_buffer_packets: int = 20):
        self.target_latency_ms = target_latency_ms
        self.max_buffer_packets = max_buffer_packets
        self.buffer = {}
        self.next_expected_seq = None
        self.concealed_packet_count = 0
        self.dropped_late_packet_count = 0

    def push_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        seq = packet.get("seq")
        timestamp = packet.get("timestamp")
        payload = packet.get("payload_bytes", b"")

        if self.next_expected_seq is None:
            self.next_expected_seq = seq

        # Check for late packet
        if seq < self.next_expected_seq:
            self.dropped_late_packet_count += 1
            return {"status": "DROPPED_LATE", "seq": seq}

        self.buffer[seq] = packet

        if len(self.buffer) > self.max_buffer_packets:
            # Drop oldest
            oldest = min(self.buffer.keys())
            del self.buffer[oldest]

        return {"status": "BUFFERED", "seq": seq, "queue_depth": len(self.buffer)}

    def pop_next_playable_frame(self) -> Dict[str, Any]:
        if self.next_expected_seq is None or not self.buffer:
            return {"status": "BUFFER_UNDERRUN", "packet": None}

        if self.next_expected_seq in self.buffer:
            pkt = self.buffer.pop(self.next_expected_seq)
            out_seq = self.next_expected_seq
            self.next_expected_seq += 1
            return {
                "status": "PLAY_ORIGINAL",
                "seq": out_seq,
                "is_concealed": False,
                "packet": pkt
            }
        else:
            # Packet loss concealment (PLC)
            missing_seq = self.next_expected_seq
            self.concealed_packet_count += 1
            self.next_expected_seq += 1
            return {
                "status": "PLAY_CONCEALED_PLC",
                "seq": missing_seq,
                "is_concealed": True,
                "packet": {"seq": missing_seq, "synthetic_silence": True}
            }
