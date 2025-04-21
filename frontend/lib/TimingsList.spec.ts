import TimingsList from "./TimingsList"
import { KEY_CODES, LYRIC_MARKERS } from "../constants";

test("TimingsList conflicts should be resolved", () => {
    const t = new TimingsList()
    t.add(0, KEY_CODES.SPACEBAR, 1.0);
    t.add(1, KEY_CODES.ENTER, 3.0);
    t.add(2, KEY_CODES.SPACEBAR, 2.5)

    expect(t.toArray()[1]).toStrictEqual([2.5, LYRIC_MARKERS.SEGMENT_START])
});

test("TimingsList can be initialized with initial timings", () => {
    const initialTimings: Array<[number, number]> = [
        [1.0, LYRIC_MARKERS.SEGMENT_START],
        [2.0, LYRIC_MARKERS.SEGMENT_END],
        [3.0, LYRIC_MARKERS.SEGMENT_START]
    ];

    const t = new TimingsList(initialTimings);

    expect(t.toArray()).toHaveLength(3);
    expect(t.toArray()).toStrictEqual(initialTimings);

    // Add additional timing
    t.add(2, KEY_CODES.ENTER, 4.0);
    expect(t.toArray()).toHaveLength(4);
    expect(t.toArray()[3]).toStrictEqual([4.0, LYRIC_MARKERS.SEGMENT_END]);
});
