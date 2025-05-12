import { createPinia, setActivePinia } from 'pinia';
import { useTimingsStore } from './timings';
import { KEY_CODES, LYRIC_MARKERS } from "../constants";

describe('Timings Store', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia());
  });

  test('conflicts should be resolved', () => {
    const timings = useTimingsStore();

    timings.add(0, KEY_CODES.SPACEBAR, 1.0);
    timings.add(1, KEY_CODES.ENTER, 3.0);
    timings.add(2, KEY_CODES.SPACEBAR, 2.5);

    expect(timings.rawTimings[1]).toStrictEqual([2.5, LYRIC_MARKERS.SEGMENT_START]);
  });

  test('length should reflect the number of timings', () => {
    const timings = useTimingsStore();

    expect(timings.length).toBe(0);

    timings.add(0, KEY_CODES.SPACEBAR, 1.0);
    expect(timings.length).toBe(1);

    timings.add(1, KEY_CODES.ENTER, 3.0);
    expect(timings.length).toBe(2);
  });

  test('last should return the most recent timing', () => {
    const timings = useTimingsStore();

    // Initial state should return null
    expect(timings.last).toStrictEqual(null);

    timings.add(0, KEY_CODES.SPACEBAR, 1.0);
    expect(timings.last).toStrictEqual([1.0, LYRIC_MARKERS.SEGMENT_START]);

    timings.add(0, KEY_CODES.ENTER, 3.0);
    expect(timings.last).toStrictEqual([3.0, LYRIC_MARKERS.SEGMENT_END]);
  });

  test('resetTimings should replace all timings', () => {
    const timings = useTimingsStore();

    timings.add(0, KEY_CODES.SPACEBAR, 1.0);
    expect(timings.length).toBe(1);

    const newTimings = [[2.0, LYRIC_MARKERS.SEGMENT_START], [5.0, LYRIC_MARKERS.SEGMENT_END]];
    timings.resetTimings(newTimings);

    expect(timings.length).toBe(2);
    expect(timings.rawTimings).toStrictEqual(newTimings);
  });

  test('timingForSegmentNum should find the correct segment start time', () => {
    const timings = useTimingsStore();

    timings.add(0, KEY_CODES.SPACEBAR, 1.0);
    timings.add(0, KEY_CODES.ENTER, 2.0);
    timings.add(1, KEY_CODES.SPACEBAR, 3.0);
    timings.add(1, KEY_CODES.ENTER, 4.0);

    expect(timings.timingForSegmentNum(0)).toBe(1.0);
    expect(timings.timingForSegmentNum(1)).toBe(3.0);
    // Segment that doesn't exist should return 0
    expect(timings.timingForSegmentNum(2)).toBe(0);
  });

  test('setCurrentSegment should truncate timings to the specified segment', () => {
    const timings = useTimingsStore();

    timings.add(0, KEY_CODES.SPACEBAR, 1.0);
    timings.add(0, KEY_CODES.ENTER, 2.0);
    timings.add(1, KEY_CODES.SPACEBAR, 3.0);
    timings.add(1, KEY_CODES.ENTER, 4.0);
    timings.add(2, KEY_CODES.SPACEBAR, 5.0);

    expect(timings.length).toBe(5);

    // Set back to segment 1
    timings.setCurrentSegment(1);

    // Should have removed the last timing (segment 2 start)
    expect(timings.length).toBe(2);
    expect(timings.last).toStrictEqual([2.0, LYRIC_MARKERS.SEGMENT_END]);

    // Set back to segment 0
    timings.setCurrentSegment(0);

    // Should have removed segment 1 timings
    expect(timings.length).toBe(0);
    expect(timings.last).toStrictEqual(null);
  });
});
