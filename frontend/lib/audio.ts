import jszip from "jszip";
import { API_HOSTNAME } from "@/constants";
import { SeparationModel } from "@/types";

// Functions for working with audio files and streams
export interface TrackSeparationResult {
    backing: Blob; // Blob of backing track
    vocals: Blob; // Blob of vocals track
}

interface PollResponse {
    finishedTrackURL: string;
}

async function pollForResult(url: string): Promise<Blob> {
    while (true) {
        const response = await fetch(url, {
            cache: 'no-cache'
        });
        const contentType = response.headers.get("content-type");

        if (contentType?.includes("application/json")) {
            await new Promise(resolve => setTimeout(resolve, 30000));
            continue;
        }

        return await response.blob();
    }
}

async function processZipResponse(zipBlob: Blob): Promise<TrackSeparationResult> {
    console.log("Received separated audio. Unzipping...");
    const zip = await jszip.loadAsync(zipBlob);
    const accompaniment = await zip.file("accompaniment.wav").async("blob").then((blob) => {
        return new Blob([blob], { type: "audio/wav" });
    });

    const vocals = await zip.file("vocals.wav").async("blob").then((blob) => {
        return new Blob([blob], { type: "audio/wav" });
    });

    return { backing: accompaniment, vocals: vocals };
}

export async function separateTrack(songFile: File, modelName: SeparationModel): Promise<TrackSeparationResult> {
    const formData = new FormData();
    formData.append("songFile", songFile);
    formData.append("modelName", modelName);
    const url = `${API_HOSTNAME}/separate_track`;
    const response = await fetch(url, {
        method: "POST",
        body: formData,
    });

    const contentType = response.headers.get("content-type");

    // The endpoint can return either a JSON response with a URL to poll for results or a direct ZIP file response
    if (contentType?.includes("application/json")) {
        const jsonResponse: PollResponse = await response.json();
        const zipBlob = await pollForResult(jsonResponse.finishedTrackURL);
        return await processZipResponse(zipBlob);
    } else {
        const zipBlob = await response.blob();
        return await processZipResponse(zipBlob);
    }
}

export default { separateTrack }