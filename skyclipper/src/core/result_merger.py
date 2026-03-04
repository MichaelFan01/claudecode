#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Result merging module for clip extraction results.

This module provides functions for parsing, merging, and processing
clip extraction results from multiple nodes.
"""

import os
import json
import glob
import time
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

from src.utils.time_utils import time_to_seconds, seconds_to_time, frame_to_seconds
from src.utils.video_utils import get_video_fps_from_clips, read_transnet_boundaries


# TransNet boundary cache (process-level cache)
_transnetCache = {}


def splitLongClipWithTransnet(clip, transnetPath, videoFps, minDuration=3, maxDurationSeconds=10):
    """
    Split long clips using TransNet boundaries intelligently.

    Args:
        clip: Original clip dictionary
        transnetPath: Path to TransNet results file
        videoFps: Video frame rate
        minDuration: Minimum duration in seconds
        maxDurationSeconds: Maximum duration in seconds

    Returns:
        list: List of split clip dictionaries
    """
    startSeconds = time_to_seconds(clip['start_time'])
    endSeconds = time_to_seconds(clip['end_time'])
    duration = endSeconds - startSeconds

    if duration <= maxDurationSeconds:
        if 'start_frame' not in clip:
            clip['start_frame'] = int(startSeconds * videoFps)
        if 'end_frame' not in clip:
            clip['end_frame'] = int(endSeconds * videoFps)
        return [clip]

    allBoundaries = read_transnet_boundaries(transnetPath, videoFps)

    clipBoundaries = [startSeconds]
    for boundary in allBoundaries:
        if startSeconds < boundary < endSeconds:
            clipBoundaries.append(boundary)
    clipBoundaries.append(endSeconds)

    if len(clipBoundaries) == 2:
        if 'start_frame' not in clip:
            clip['start_frame'] = int(startSeconds * videoFps)
        if 'end_frame' not in clip:
            clip['end_frame'] = int(endSeconds * videoFps)
        return [clip]

    resultClips = []
    currentStart = startSeconds
    currentStartIdx = 0

    while currentStartIdx < len(clipBoundaries) - 1:
        bestEndIdx = currentStartIdx + 1

        for endIdx in range(currentStartIdx + 1, len(clipBoundaries)):
            segmentDuration = clipBoundaries[endIdx] - currentStart

            if segmentDuration <= maxDurationSeconds:
                bestEndIdx = endIdx
            else:
                break

        segmentDuration = clipBoundaries[bestEndIdx] - currentStart
        if segmentDuration < minDuration and bestEndIdx < len(clipBoundaries) - 1:
            nextDuration = clipBoundaries[bestEndIdx + 1] - currentStart
            if nextDuration <= maxDurationSeconds:
                bestEndIdx += 1

        newClip = clip.copy()
        newClip['start_time'] = seconds_to_time(currentStart)
        newClip['end_time'] = seconds_to_time(clipBoundaries[bestEndIdx])
        newClip['start_frame'] = int(currentStart * videoFps)
        newClip['end_frame'] = int(clipBoundaries[bestEndIdx] * videoFps)

        resultClips.append(newClip)

        currentStart = clipBoundaries[bestEndIdx]
        currentStartIdx = bestEndIdx

    return resultClips


def splitLongClipHard(clip, videoFps=30.0, maxDurationSeconds=10):
    """
    Hard split long clips when no TransNet boundaries are available.

    Args:
        clip: Original clip dictionary
        videoFps: Video frame rate
        maxDurationSeconds: Maximum duration in seconds

    Returns:
        list: List of split clip dictionaries
    """
    startSeconds = time_to_seconds(clip['start_time'])
    endSeconds = time_to_seconds(clip['end_time'])
    duration = endSeconds - startSeconds

    if duration <= maxDurationSeconds:
        return [clip]

    resultClips = []
    currentStart = startSeconds
    partIndex = 0

    while currentStart < endSeconds:
        currentEnd = min(currentStart + maxDurationSeconds, endSeconds)

        newClip = clip.copy()
        newClip['start_time'] = seconds_to_time(currentStart)
        newClip['end_time'] = seconds_to_time(currentEnd)
        newClip['start_frame'] = int(currentStart * videoFps)
        newClip['end_frame'] = int(currentEnd * videoFps)
        newClip['event'] = clip.get('event', '') + (f' [Part {partIndex + 1}]' if partIndex > 0 else '')

        resultClips.append(newClip)
        currentStart = currentEnd
        partIndex += 1

    return resultClips


def mergeClipsByDuration(clips, videoFps=30.0, transnetPath=None, minDuration=3, maxDurationSeconds=10):
    """
    Merge clips by duration and split long clips using TransNet boundaries.

    Args:
        clips: List of original clip dictionaries
        videoFps: Video frame rate
        transnetPath: Path to TransNet results file
        minDuration: Minimum duration in seconds
        maxDurationSeconds: Maximum duration in seconds

    Returns:
        list: List of merged clip dictionaries
    """
    if not clips:
        return []

    splitClips = []
    for clip in clips:
        if transnetPath:
            splitClips.extend(splitLongClipWithTransnet(
                clip, transnetPath, videoFps, minDuration, maxDurationSeconds
            ))
        else:
            splitClips.extend(splitLongClipHard(clip, videoFps, maxDurationSeconds))

    if not splitClips:
        return []

    actionGroups = []
    currentGroup = [splitClips[0]]

    for i in range(1, len(splitClips)):
        currentClip = splitClips[i]
        prevClip = splitClips[i-1]

        startSeconds = time_to_seconds(currentClip['start_time'])
        prevEndSeconds = time_to_seconds(prevClip['end_time'])
        isAdjacent = abs(startSeconds - prevEndSeconds) < 0.5

        currentAction = currentClip.get('action_id', 0)
        prevAction = prevClip.get('action_id', 0)

        if currentAction == prevAction and isAdjacent:
            currentGroup.append(currentClip)
        else:
            actionGroups.append(currentGroup)
            currentGroup = [currentClip]

    actionGroups.append(currentGroup)

    mergedClips = []
    for group in actionGroups:
        if len(group) == 1:
            clip = group[0].copy()
            if 'start_frame' not in clip:
                clip['start_frame'] = int(time_to_seconds(clip['start_time']) * videoFps)
            if 'end_frame' not in clip:
                clip['end_frame'] = int(time_to_seconds(clip['end_time']) * videoFps)
            mergedClips.append(clip)
        else:
            mergedClip = group[0].copy()
            if 'start_frame' not in mergedClip:
                mergedClip['start_frame'] = int(time_to_seconds(mergedClip['start_time']) * videoFps)

            for i in range(1, len(group)):
                nextClip = group[i]

                startSeconds = time_to_seconds(mergedClip['start_time'])
                endSeconds = time_to_seconds(nextClip['end_time'])
                mergedDuration = endSeconds - startSeconds

                if mergedDuration <= maxDurationSeconds:
                    mergedClip['end_time'] = nextClip['end_time']
                    mergedClip['end_frame'] = nextClip.get('end_frame', int(endSeconds * videoFps))
                    if mergedClip.get('event') and nextClip.get('event'):
                        mergedClip['event'] = mergedClip['event']
                    if not mergedClip.get('action_desc') and nextClip.get('action_desc'):
                        mergedClip['action_desc'] = nextClip.get('action_desc')
                else:
                    mergedClips.append(mergedClip)
                    mergedClip = nextClip.copy()
                    if 'start_frame' not in mergedClip:
                        mergedClip['start_frame'] = int(time_to_seconds(mergedClip['start_time']) * videoFps)
                    if 'end_frame' not in mergedClip:
                        mergedClip['end_frame'] = int(time_to_seconds(mergedClip['end_time']) * videoFps)

            if 'end_frame' not in mergedClip:
                mergedClip['end_frame'] = int(time_to_seconds(mergedClip['end_time']) * videoFps)
            mergedClips.append(mergedClip)

    for clip in mergedClips:
        if 'start_frame' not in clip:
            clip['start_frame'] = int(time_to_seconds(clip['start_time']) * videoFps)
        if 'end_frame' not in clip:
            clip['end_frame'] = int(time_to_seconds(clip['end_time']) * videoFps)

    finalClips = []
    for clip in mergedClips:
        startSeconds = time_to_seconds(clip['start_time'])
        endSeconds = time_to_seconds(clip['end_time'])
        duration = endSeconds - startSeconds

        if len(finalClips) > 0:
            lastClip = finalClips[-1]

            lastEnd = time_to_seconds(lastClip['end_time'])
            currStart = time_to_seconds(clip['start_time'])
            isAdjacent = abs(currStart - lastEnd) < 0.5

            currentAction = clip.get('action_id', 0)
            lastAction = lastClip.get('action_id', 0)

            lastDuration = time_to_seconds(lastClip['end_time']) - time_to_seconds(lastClip['start_time'])

            shouldMerge = False
            if lastAction == currentAction and isAdjacent:
                shouldMerge = True
            elif isAdjacent and (duration < minDuration or lastDuration < minDuration):
                shouldMerge = True

            if shouldMerge:
                mergedStart = time_to_seconds(lastClip['start_time'])
                mergedEnd = time_to_seconds(clip['end_time'])
                mergedDuration = mergedEnd - mergedStart

                if mergedDuration <= maxDurationSeconds:
                    lastClip['end_time'] = clip['end_time']
                    lastClip['end_frame'] = clip.get('end_frame', int(mergedEnd * videoFps))
                    if not lastClip.get('action_desc') and clip.get('action_desc'):
                        lastClip['action_desc'] = clip.get('action_desc')
                    continue

        if 'start_frame' not in clip:
            clip['start_frame'] = int(time_to_seconds(clip['start_time']) * videoFps)
        if 'end_frame' not in clip:
            clip['end_frame'] = int(time_to_seconds(clip['end_time']) * videoFps)
        finalClips.append(clip)

    allBoundaries = read_transnet_boundaries(transnetPath, videoFps) if transnetPath else []

    balancedClips = []
    i = 0

    while i < len(finalClips):
        currentClip = finalClips[i]
        currentStart = time_to_seconds(currentClip['start_time'])
        currentEnd = time_to_seconds(currentClip['end_time'])
        currentDuration = currentEnd - currentStart

        if i < len(finalClips) - 1:
            nextClip = finalClips[i + 1]
            nextStart = time_to_seconds(nextClip['start_time'])
            nextEnd = time_to_seconds(nextClip['end_time'])
            nextDuration = nextEnd - nextStart

            isAdjacent = abs(currentEnd - nextStart) < 0.5

            totalDuration = currentDuration + nextDuration
            currentAction = currentClip.get('action_id', 0)
            nextAction = nextClip.get('action_id', 0)

            shouldRebalance = False
            if isAdjacent and totalDuration <= maxDurationSeconds * 2:
                if currentDuration < minDuration or nextDuration < minDuration:
                    shouldRebalance = True
                elif max(currentDuration, nextDuration) / min(currentDuration, nextDuration) > 3:
                    shouldRebalance = True

            if shouldRebalance:
                if totalDuration <= maxDurationSeconds:
                    mergedClip = currentClip.copy()
                    mergedClip['end_time'] = nextClip['end_time']
                    mergedClip['end_frame'] = nextClip.get('end_frame', int(nextEnd * videoFps))
                    if 'start_frame' not in mergedClip:
                        mergedClip['start_frame'] = int(currentStart * videoFps)

                    if not mergedClip.get('action_desc') and nextClip.get('action_desc'):
                        mergedClip['action_desc'] = nextClip.get('action_desc')

                    balancedClips.append(mergedClip)
                    i += 2
                    continue
                else:
                    segmentBoundaries = [currentStart]
                    if allBoundaries:
                        for boundary in allBoundaries:
                            if currentStart < boundary < nextEnd:
                                segmentBoundaries.append(boundary)
                    segmentBoundaries.append(nextEnd)

                    if len(segmentBoundaries) > 2:
                        bestBoundary = None
                        minImbalance = float('inf')

                        for boundary in segmentBoundaries[1:-1]:
                            firstDuration = boundary - currentStart
                            secondDuration = nextEnd - boundary

                            if (minDuration <= firstDuration <= maxDurationSeconds and
                                minDuration <= secondDuration <= maxDurationSeconds):
                                imbalance = abs(firstDuration - secondDuration)
                                if imbalance < minImbalance:
                                    minImbalance = imbalance
                                    bestBoundary = boundary

                        if bestBoundary:
                            newBoundary = bestBoundary
                        else:
                            targetBoundary = currentStart + totalDuration / 2.0
                            newBoundary = min(segmentBoundaries[1:-1],
                                             key=lambda x: abs(x - targetBoundary))
                    else:
                        newBoundary = currentStart + totalDuration / 2.0

                    rebalancedCurrent = currentClip.copy()
                    rebalancedCurrent['end_time'] = seconds_to_time(newBoundary)
                    rebalancedCurrent['end_frame'] = int(newBoundary * videoFps)

                    rebalancedNext = nextClip.copy()
                    rebalancedNext['start_time'] = seconds_to_time(newBoundary)
                    rebalancedNext['start_frame'] = int(newBoundary * videoFps)

                    balancedClips.append(rebalancedCurrent)
                    balancedClips.append(rebalancedNext)
                    i += 2
                    continue

        if 'start_frame' not in currentClip:
            currentClip['start_frame'] = int(currentStart * videoFps)
        if 'end_frame' not in currentClip:
            currentClip['end_frame'] = int(currentEnd * videoFps)
        balancedClips.append(currentClip)
        i += 1

    for clip in balancedClips:
        if 'start_frame' not in clip or clip.get('start_frame', 0) == 0:
            clip['start_frame'] = int(time_to_seconds(clip['start_time']) * videoFps)
        if 'end_frame' not in clip or clip.get('end_frame', 0) == 0:
            clip['end_frame'] = int(time_to_seconds(clip['end_time']) * videoFps)

    for i, clip in enumerate(balancedClips):
        clip['clip_index'] = i

    return balancedClips


def processSingleNodeFile(argsTuple):
    """
    Process a single node file and generate shot and scene level temporary files.

    Args:
        argsTuple: Tuple containing (nodeFile, tempDir, resultsDir, minDurationSeconds, maxDurationSeconds)

    Returns:
        tuple: (nodeId, shotCount, sceneCount, errorCount)
    """
    from src.utils.xml_parser import parse_xml_clips

    nodeFile, tempDir, resultsDir, minDurationSeconds, maxDurationSeconds = argsTuple
    nodeId = os.path.basename(nodeFile).replace("node_", "").replace(".jsonl", "")

    shotTempFile = os.path.join(resultsDir, f"node_{nodeId}_shot.jsonl")
    sceneTempFile = os.path.join(resultsDir, f"node_{nodeId}_scene.jsonl")

    shotCount = 0
    sceneCount = 0
    errorCount = 0

    try:
        with open(nodeFile, 'r', encoding='utf-8') as f_in, \
             open(shotTempFile, 'w', encoding='utf-8') as f_shot, \
             open(sceneTempFile, 'w', encoding='utf-8') as f_scene:

            for lineNum, line in enumerate(f_in, 1):
                if not line.strip():
                    continue

                try:
                    data = json.loads(line.strip())
                    videoId = data.get('id')

                    if not videoId:
                        errorCount += 1
                        continue

                    if 'clips' not in data or not data['clips']:
                        if 'llm_output' in data and data['llm_output']:
                            try:
                                parsedClips = parse_xml_clips(data['llm_output'])
                                if parsedClips:
                                    data['clips'] = parsedClips
                            except Exception as e:
                                errorCount += 1
                                continue

                    if 'clips' not in data or not data['clips']:
                        errorCount += 1
                        continue

                    videoMeta = data.get('video_meta', {})
                    videoFps = get_video_fps_from_clips(data['clips'], videoMeta)

                    for clip in data['clips']:
                        if 'start_frame' not in clip or clip.get('start_frame', 0) == 0:
                            try:
                                startSeconds = time_to_seconds(clip['start_time'])
                                clip['start_frame'] = int(startSeconds * videoFps)
                            except:
                                clip['start_frame'] = 0
                        if 'end_frame' not in clip or clip.get('end_frame', 0) == 0:
                            try:
                                endSeconds = time_to_seconds(clip['end_time'])
                                clip['end_frame'] = int(endSeconds * videoFps)
                            except:
                                clip['end_frame'] = 0

                    shotData = data.copy()

                    if 'llm_output' in shotData:
                        del shotData['llm_output']
                    if 'prompt' in shotData:
                        del shotData['prompt']

                    f_shot.write(json.dumps(shotData, ensure_ascii=False) + '\n')
                    shotCount += 1

                    sceneData = data.copy()
                    if 'clips' in sceneData and sceneData['clips']:
                        transnetPath = sceneData.get('transnet_path', '')

                        if transnetPath:
                            if transnetPath.startswith("/maindata/data/shared/public/dongyang.zhang/"):
                                transnetPath = transnetPath.replace(
                                    "/maindata/data/shared/public/dongyang.zhang/",
                                    "/ai-video-nas-sh-b-2/dongyang/maindata/",
                                    1
                                )

                        mergedClips = mergeClipsByDuration(
                            sceneData['clips'],
                            videoFps=videoFps,
                            transnetPath=transnetPath,
                            minDuration=minDurationSeconds,
                            maxDurationSeconds=maxDurationSeconds
                        )
                        sceneData['clips'] = mergedClips

                    if 'llm_output' in sceneData:
                        del sceneData['llm_output']
                    if 'prompt' in sceneData:
                        del sceneData['prompt']

                    f_scene.write(json.dumps(sceneData, ensure_ascii=False) + '\n')
                    sceneCount += 1

                except json.JSONDecodeError as e:
                    errorCount += 1
                    continue
                except Exception as e:
                    errorCount += 1
                    continue

    except Exception as e:
        return (nodeId, 0, 0, -1)

    return (nodeId, shotCount, sceneCount, errorCount)


def mergeTempFiles(resultsDir, outputPath, filePattern):
    """
    Merge all temporary files into the final output file.

    Args:
        resultsDir: Results temporary directory
        outputPath: Final output file path
        filePattern: File matching pattern (e.g., "node_*_shot.jsonl")
    """
    pattern = os.path.join(resultsDir, filePattern)
    tempFiles = sorted(glob.glob(pattern))

    if not tempFiles:
        print(f"Warning: No temporary files found matching: {filePattern}")
        return 0

    totalCount = 0
    seenIds = set()
    duplicateCount = 0

    with open(outputPath, 'w', encoding='utf-8') as f_out:
        for tempFile in tqdm(tempFiles, desc=f"Merging {filePattern}"):
            try:
                with open(tempFile, 'r', encoding='utf-8') as f_in:
                    for line in f_in:
                        if not line.strip():
                            continue

                        try:
                            data = json.loads(line.strip())
                            uniqueId = data.get('segment_id') or data.get('id')

                            if uniqueId in seenIds:
                                duplicateCount += 1
                                continue

                            seenIds.add(uniqueId)
                            f_out.write(line)
                            totalCount += 1

                        except:
                            f_out.write(line)
                            totalCount += 1

            except Exception as e:
                print(f"  Error: Failed to read temporary file {tempFile}: {e}")
                continue

    if duplicateCount > 0:
        print(f"  Removed duplicates: {duplicateCount} records")

    return totalCount


def parallelProcessNodeFiles(tempDir, resultsDir, minDurationSeconds=3, maxDurationSeconds=10, numWorkers=None):
    """
    Process all node files in parallel and generate shot and scene temporary files.

    Args:
        tempDir: Input temporary directory path
        resultsDir: Output results directory path
        minDurationSeconds: Minimum duration for scene merging in seconds
        maxDurationSeconds: Maximum duration for scene merging in seconds
        numWorkers: Number of parallel processes, defaults to CPU count

    Returns:
        dict: Processing statistics
    """
    print(f"=" * 60)
    print(f"Processing node files in parallel...")
    print(f"Input directory: {tempDir}")
    print(f"Output directory: {resultsDir}")
    print(f"Duration range: {minDurationSeconds}-{maxDurationSeconds} seconds")
    print(f"=" * 60)

    os.makedirs(resultsDir, exist_ok=True)

    pattern = os.path.join(tempDir, "node_*.jsonl")
    allFiles = glob.glob(pattern)
    nodeFiles = [f for f in allFiles if not (f.endswith('_shot.jsonl') or f.endswith('_scene.jsonl'))]
    nodeFiles = sorted(nodeFiles)

    if not nodeFiles:
        print(f"Error: No node_*.jsonl files found in {tempDir}")
        return {}

    print(f"Found {len(nodeFiles)} node files")
    for f in nodeFiles[:5]:
        fileSize = os.path.getsize(f)
        print(f"  - {os.path.basename(f)}: {fileSize:,} bytes")
    if len(nodeFiles) > 5:
        print(f"  ... and {len(nodeFiles) - 5} more files")

    if numWorkers is None:
        numWorkers = min(os.cpu_count(), len(nodeFiles))

    print(f"\nUsing {numWorkers} processes for parallel processing...")
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    argsList = [(nodeFile, tempDir, resultsDir, minDurationSeconds, maxDurationSeconds) for nodeFile in nodeFiles]

    startTime = time.time()

    results = []
    with ProcessPoolExecutor(max_workers=numWorkers) as executor:
        futureToFile = {executor.submit(processSingleNodeFile, args): args[0] for args in argsList}

        with tqdm(total=len(nodeFiles), desc="Total progress", position=0) as pbar:
            for future in as_completed(futureToFile):
                nodeFile = futureToFile[future]
                nodeId = os.path.basename(nodeFile).replace("node_", "").replace(".jsonl", "")
                try:
                    result = future.result()
                    results.append(result)
                    pbar.set_description(f"Total progress (just completed: Node {result[0]})")
                    pbar.update(1)
                except Exception as e:
                    pbar.set_description(f"Total progress (Node {nodeId} error)")
                    pbar.update(1)

    endTime = time.time()
    elapsedTime = endTime - startTime

    totalShot = 0
    totalScene = 0
    totalErrors = 0
    failedNodes = []

    for nodeId, shotCount, sceneCount, errorCount in results:
        if errorCount == -1:
            failedNodes.append(nodeId)
        else:
            totalShot += shotCount
            totalScene += sceneCount
            totalErrors += errorCount

    print(f"\n" + "=" * 60)
    print(f"Parallel processing complete!")
    print(f"  Time elapsed: {elapsedTime:.2f} seconds ({elapsedTime/60:.2f} minutes)")
    print(f"  Processing speed: {len(nodeFiles)/elapsedTime:.2f} files/second")
    print(f"  Shot records: {totalShot}")
    print(f"  Scene records: {totalScene}")
    print(f"  Error records: {totalErrors}")
    if failedNodes:
        print(f"  Failed nodes: {', '.join(failedNodes)}")
    print(f"=" * 60)

    return {
        'total_shot': totalShot,
        'total_scene': totalScene,
        'total_errors': totalErrors,
        'failed_nodes': failedNodes,
        'elapsed_time': elapsedTime
    }


# Snake_case aliases for backward compatibility
split_long_clip_with_transnet = splitLongClipWithTransnet
split_long_clip_hard = splitLongClipHard
merge_clips_by_duration = mergeClipsByDuration
process_single_node_file = processSingleNodeFile
merge_temp_files = mergeTempFiles
parallel_process_node_files = parallelProcessNodeFiles
