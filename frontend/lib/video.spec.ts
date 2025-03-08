import { describe, it, expect } from 'vitest';
import { parseYouTubeTitle } from './video';

describe('Video Library', () => {

    it('parseYouTubeTitle handles titles without author info', () => {
        expect(parseYouTubeTitle({ title: 'The Bolks singing Squibble Doo Dah' })).toEqual(['', 'The Bolks singing Squibble Doo Dah']);
    });

    it('parseYouTubeTitle parses author and title correctly', () => {
        const expected = ['The Bolks', 'Squibble Doo Dah'];
        expect(parseYouTubeTitle({ author: 'The Bolks', title: 'Squibble Doo Dah' })).toEqual(expected);
    });
});