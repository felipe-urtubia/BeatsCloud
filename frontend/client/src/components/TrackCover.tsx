import React, { useState } from 'react';
import placeholder from '../assets/track-cover-placeholder.svg';

type Props = Omit<
  React.ImgHTMLAttributes<HTMLImageElement>,
  'onError'
>;

function CoverImage({ src, ...props }: Props) {
  const [failed, setFailed] = useState(false);

  return (
    <img
      {...props}
      src={failed ? placeholder : (src || placeholder)}
      onError={() => {
        if (!failed && src && src !== placeholder) {
          setFailed(true);
        }
      }}
    />
  );
}

export function TrackCover(props: Props) {
  return <CoverImage key={props.src} {...props} />;
}
