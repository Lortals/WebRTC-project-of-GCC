import argparse
import asyncio
import logging
import math

import cv2
import numpy
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
from av import VideoFrame


async def read_stats_offer(pc, i):
    # check stats
    f = open('log_send.txt','a+')
    report = await pc.getSenders()[0].getStats()
    report_keys = list(report.keys())
    print(f'stats show {i}--------------------------------', file=f)
    print('sending end:', file=f)
    print(f'time of sending = {report[report_keys[0]].timestamp}', file=f)
    print(f'bytes sent = {report[report_keys[1]].bytesSent}', file=f)
    print(f'packets sent = {report[report_keys[1]].packetsSent}', file=f)

    print(f'rtt = {report[report_keys[0]].roundTripTime}', file=f)
    # receiver stats
    print('receiving end:',file=f)
    print(f'packets received = {report[report_keys[0]].packetsReceived}', file=f)
    print(f'packets lost = {report[report_keys[0]].packetsLost}', file=f)
    print(f'jitter = {report[report_keys[0]].jitter}', file=f)
    print('stats show--------------------------------',end="\n", file=f) 
    # stats report complete
    f.close()
    
    
async def read_stats_answer(pc):
    # check stats
    report = await pc.getStats()
    report_keys = list(report.keys())
    print('stats show--------------------------------')
    print(f'rtt = {report[report_keys[0]].roundTripTime}')
    print(f'received packets = {report[report_keys[4]].packetsReceived}')
    print(f'lost packets = {report[report_keys[4]].packetsLost}')
    print(f'jitter = {report[report_keys[4]].jitter}')
    print('stats show--------------------------------',end="\n") 
    # stats report complete


async def run(pc, player, recorder, signaling, role):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)
        

    @pc.on("track")
    def on_track(track):
        print("Receiving %s" % track.kind)
        recorder.addTrack(track)

    # connect signaling
    await signaling.connect()
    
    # 己方为offerer，则创建offer并“发送localdescription
    if role == "offer":
        # send offer
        add_tracks()
        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)
    # consume signaling
    i = 0
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()
            if obj.type == "answer":
                # check stats
                # f = open('log_send.txt','a+')
                await asyncio.sleep(1.5)
                while True:
                    await read_stats_offer(pc, i)
                    # print(f"this is the estimated bitrate{pc.getSenders()[0].__encoder.target_bitrate}")
                    await asyncio.sleep(1)
                    i += 1
                # stats report complete
            if obj.type == "offer":
                # send answer
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
                # check stats
                # allow media to flow long enough to collect stats
                await asyncio.sleep(5)
                while True:
                    await asyncio.sleep(1)
                    await read_stats_answer(pc)
                # stats report complete
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--play-from", help="Read the media from a file and sent it."),
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,  
                    format='%(asctime)s.%(msecs)03d %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',  
                    datefmt='%a, %d %b %Y %H:%M:%S',  
                    filename='test.log',  
                    filemode='w')

    # create signaling and peer connection
    signaling = create_signaling(args)
    pc = RTCPeerConnection()

    # create media source
    if args.play_from:
        player = MediaPlayer(args.play_from)
    else:
        player = None

    # create media sink
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
    else:
        recorder = MediaBlackhole()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                player=player,
                recorder=recorder,
                signaling=signaling,
                role=args.role,
            )
            
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())



