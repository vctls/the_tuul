import jszip from "jszip";
import { API_HOSTNAME } from "@/constants";
import { SeparationModel } from "@/types";

// Functions for working with audio files and streams
export interface TrackSeparationResult {
    backing: string; // Blob URL of backing track
    vocals: string; // Blob URL of vocals track
}

export async function separateTrack(songFile: File, modelName: SeparationModel): Promise<TrackSeparationResult> {
    // Separate the track and return a blob url of the accompaniment stem data
    const formData = new FormData();
    formData.append("songFile", songFile);
    formData.append("modelName", modelName);
    const url = `${API_HOSTNAME}/separate_track`;
    const response = await fetch(url, {
        method: "POST",
        body: formData,
    });
    const zipContents = await response.blob();
    console.log("Received separated audio. Unzipping...");
    const zip = await jszip.loadAsync(zipContents);
    const contents = await zip.file("accompaniment.wav").async("blob");
    const backingUrl = URL.createObjectURL(contents);
    const vocals = await zip.file("vocals.wav").async("blob");
    const vocalsUrl = URL.createObjectURL(vocals);
    console.log("Got backing URL: ", backingUrl);

    return { backing: backingUrl, vocals: vocalsUrl };
}

export default { separateTrack }