/* Owned clear-media acceptance fixtures. Run in the actual Archium APK. */
function assessPlayback(sample, videoRequired) {
    return sample.error == null && Number.isFinite(sample.before) &&
        Number.isFinite(sample.after) && sample.after > sample.before + 0.1 &&
        (!videoRequired || (Number.isFinite(sample.frames) && sample.frames > 0));
}

if (typeof module !== 'undefined') module.exports = {assessPlayback};

if (typeof document !== 'undefined') {
    const player = document.getElementById('player');
    const output = document.getElementById('output');
    const start = document.getElementById('run');
    const cases = [
        {name:'MP4 · H.264 + AAC', file:'avc-aac.mp4', video:true},
        {name:'M4A · AAC', file:'aac.m4a', video:false},
        {name:'WebM · VP8 + Opus', file:'vp8-opus.webm', video:true},
        {name:'WebM · VP9 + Opus', file:'vp9-opus.webm', video:true},
        {name:'WebM · AV1 + Opus', file:'av1-opus.webm', video:true},
        {name:'MP4 · seek', file:'avc-aac.mp4', video:true, seek:true},
        {name:'MSE · fragmented H.264 + AAC', file:'avc-aac-fragmented.mp4', video:true, mse:true},
        {name:'HLS · H.264 + AAC', file:'playlist.m3u8', video:true}
    ];
    let lastReport;

    function once(target, event, pending, timeout = 15000) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => finish(new Error('Timeout: ' + event)), timeout);
            const cancel = () => { clean(); resolve(); };
            pending.add(cancel);
            function clean() {
                clearTimeout(timer); target.removeEventListener(event, success);
                target.removeEventListener('error', failed);
                pending.delete(cancel);
            }
            function finish(error) { clean(); error ? reject(error) : resolve(); }
            function success() { finish(); }
            function failed() { finish(new Error('Media error: ' + (player.error ? player.error.code : 'unknown'))); }
            target.addEventListener(event, success); target.addEventListener('error', failed);
        });
    }

    function withTimeout(promise, label, timeout = 15000) {
        let timer;
        return Promise.race([promise, new Promise((resolve, reject) => {
            timer = setTimeout(() => reject(new Error('Timeout: ' + label)), timeout);
        })]).finally(() => clearTimeout(timer));
    }

    function show() { output.textContent = JSON.stringify(lastReport, null, 2); }

    async function playback(test) {
        let objectUrl;
        const pending = new Set();
        const wait = (target, event) => once(target, event, pending);
        const frames = () => player.getVideoPlaybackQuality
            ? player.getVideoPlaybackQuality().totalVideoFrames : player.webkitDecodedFrameCount;
        player.pause(); player.removeAttribute('src'); player.load(); player.muted = true;
        try {
            if (test.mse) {
                const mime = 'video/mp4; codecs="avc1.42C01E, mp4a.40.2"';
                if (!window.MediaSource || !MediaSource.isTypeSupported(mime)) throw new Error('MSE codec unavailable');
                const source = new MediaSource();
                const opened = wait(source, 'sourceopen');
                objectUrl = URL.createObjectURL(source); player.src = objectUrl;
                await opened;
                const response = await withTimeout(fetch('data/' + test.file), 'MSE fetch');
                if (!response.ok) throw new Error('HTTP ' + response.status);
                const data = await withTimeout(response.arrayBuffer(), 'MSE bytes');
                const buffer = source.addSourceBuffer(mime);
                const appended = wait(buffer, 'updateend'); buffer.appendBuffer(data); await appended;
                source.endOfStream();
                if (player.readyState < 1) await wait(player, 'loadedmetadata');
            } else {
                const loaded = wait(player, 'loadedmetadata');
                player.src = 'data/' + test.file; player.load(); await loaded;
            }
            if (test.seek) {
                const seeked = wait(player, 'seeked');
                player.currentTime = 1; await seeked;
                if (Math.abs(player.currentTime - 1) > 0.25) throw new Error('Seek did not reach target');
            }
            const before = player.currentTime;
            const beforeFrames = frames();
            const ended = wait(player, 'ended');
            // Observe both promises even if play() rejects, so timeout/error cannot leak.
            await Promise.all([ended, withTimeout(player.play(), 'play')]);
            const sample = {before, after:player.currentTime,
                frames:frames() - beforeFrames,
                error:player.error ? player.error.code : null};
            if (!assessPlayback(sample, test.video)) throw new Error('Playback evidence failed: ' + JSON.stringify(sample));
            return {name:test.name, status:'PASS', evidence:sample};
        } finally {
            for (const cancel of pending) cancel();
            player.pause(); player.removeAttribute('src'); player.load();
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        }
    }

    start.addEventListener('click', async () => {
        start.disabled = true;
        lastReport = {userAgent:navigator.userAgent, results:[],
            browserIdentity:'REQUIRES_EXTERNAL_APK_VERIFICATION',
            hardwareDecode:'NOT_VERIFIED', audibleAudio:'PENDING_MANUAL',
            fullscreen:'PENDING_MANUAL', pictureInPicture:'PENDING_MANUAL',
            drm:'NOT_TESTED', automatedStatus:'RUNNING'};
        show();
        try {
            for (const test of cases) {
                try { lastReport.results.push(await playback(test)); }
                catch (error) { lastReport.results.push({name:test.name, status:'FAIL', error:String(error)}); }
                show();
            }
            lastReport.automatedStatus = lastReport.results.every(r => r.status === 'PASS') ? 'PASS' : 'FAIL';
        } finally {
            player.src = 'data/avc-aac.mp4'; player.muted = false;
            start.disabled = false; show();
        }
    });

    document.getElementById('save').addEventListener('click', () => {
        if (!lastReport) return;
        const blob = new Blob([JSON.stringify(lastReport, null, 2)], {type:'application/json'});
        const url = URL.createObjectURL(blob); const link = document.createElement('a');
        link.href = url; link.download = 'archium-media-results.json'; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
}
