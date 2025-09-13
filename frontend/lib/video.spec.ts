import { parseYouTubeTitle, fetchYouTubeVideo } from './video';

// Mock fetch globally
global.fetch = vi.fn();

describe('Video Library', () => {

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('parseYouTubeTitle handles titles without author info', () => {
        expect(parseYouTubeTitle({ title: 'The Bolks singing Squibble Doo Dah' })).toEqual(['', 'The Bolks singing Squibble Doo Dah']);
    });

    it('parseYouTubeTitle parses author and title correctly', () => {
        const expected = ['The Bolks', 'Squibble Doo Dah'];
        expect(parseYouTubeTitle({ author: 'The Bolks', title: 'Squibble Doo Dah' })).toEqual(expected);
    });

    it('fetchYouTubeVideo throws error when polling endpoint returns error JSON', async () => {
        const mockFetch = fetch as any;
        
        // Mock initial response with polling URL
        const initialResponse = {
            status: 200,
            headers: {
                get: vi.fn().mockReturnValue('application/json'),
            },
            json: vi.fn().mockResolvedValue({
                finishedDownloadURL: 'http://example.com/poll-url'
            }),
        };

        // Mock polling response with error JSON
        const errorResponse = {
            status: 200,
            headers: {
                get: vi.fn().mockReturnValue('application/json'),
            },
            blob: vi.fn().mockResolvedValue(new Blob([JSON.stringify({
                success: false,
                error: 'No route to host - unable to reach: YouTube servers'
            })], { type: 'application/json' })),
        };

        mockFetch
            .mockResolvedValueOnce(initialResponse as any)
            .mockResolvedValueOnce(errorResponse as any);

        await expect(fetchYouTubeVideo('https://www.youtube.com/watch?v=test'))
            .rejects
            .toThrow('No route to host - unable to reach: YouTube servers');
    });
});