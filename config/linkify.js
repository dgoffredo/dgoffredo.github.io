window.onload = () => {
    Array.from(document.getElementsByTagName('img')).forEach(img => {
        // If the src of the img ends with "_small.jpg", remove the <img> from
        // its <p> parent, wrap the <img> in an <a>, and then put the <a> into
        // the <p>.  That is, wrap the <img> in a link.
        if (!img.src.endsWith('_small.jpg')) {
            return;  // doesn't need to be made into a "click to enlarge"
        }

        img.className = 'thumbnail';  // for styling

        const p = img.parentNode,
              link = document.createElement('a');

        //             new   old
        p.replaceChild(link, img);

        link.setAttribute('href', img.src.replace(/_small\.jpg$/, '.jpg'));
        link.appendChild(img);
    });
}
