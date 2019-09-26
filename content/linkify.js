window.onload = () => {
    Array.from(document.getElementsByTagName('img')).forEach(img => {
        // Remove the <img> from its <p> parent, wrap the <img> in an <a>, and
        // then put the <a> into the <p>.  That is, wrap the <img> in a link.
        if (!img.src.endsWith('_small.jpg')) {
            return;  // doesn't need to be made into a "click to enlarge"
        }

        const p = img.parentNode;
        p.removeChild(img);

        const link = document.createElement('a');
        link.setAttribute('href', img.src.replace(/_small\.jpg$/, '.jpg'));
        link.appendChild(img);
        p.appendChild(link);
    });
}