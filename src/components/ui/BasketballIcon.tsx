import React from 'react';

const BasketballIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg width="66" height="66" viewBox="0 0 66 66" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <path d="M3.5 43.5H22.5V62.5H9C5.96243 62.5 3.5 60.0376 3.5 57V43.5Z" fill="#E87503" stroke="black"/>
    <path d="M43.5 43.5H62.5V57C62.5 60.0376 60.0376 62.5 57 62.5H43.5V43.5Z" fill="#E87503" stroke="black"/>
    <rect x="23.5" y="43.5" width="19" height="19" fill="#E87503" stroke="black"/>
    <rect x="3.5" y="23.5" width="19" height="19" fill="#E87503" stroke="black"/>
    <rect x="43.5" y="23.5" width="19" height="19" fill="#E87503" stroke="black"/>
    <rect x="23.5" y="23.5" width="19" height="19" fill="#E87503" stroke="black"/>
    <path d="M9 3.5H22.5V22.5H3.5V9C3.5 5.96243 5.96243 3.5 9 3.5Z" fill="#E87503" stroke="black"/>
    <path d="M43.5 3.5H57C60.0376 3.5 62.5 5.96243 62.5 9V22.5H43.5V3.5Z" fill="#E87503" stroke="black"/>
    <rect x="23.5" y="3.5" width="19" height="19" fill="#E87503" stroke="black"/>
    <rect x="1.5" y="1.5" width="63" height="63" rx="7.5" stroke="black" strokeWidth="3"/>
  </svg>
);

export default BasketballIcon;

// Add these sizes for different use cases
const sizes = {
    favicon: 32,
    apple: 180,
    og: { width: 1200, height: 630 }
  };
  
  // For OG image, center the basketball in a larger canvas
  const OGImage = () => (
    <svg width={sizes.og.width} height={sizes.og.height} viewBox={`0 0 ${sizes.og.width} ${sizes.og.height}`} fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width={sizes.og.width} height={sizes.og.height} fill="white"/>
      <g transform={`translate(${(sizes.og.width - 200) / 2} ${(sizes.og.height - 200) / 2})`}>
        {/* Scale up the basketball icon to 200x200 */}
        <g transform="scale(3.03)">
          {/* Your existing basketball paths here */}
          <path d="M3.5 43.5H22.5V62.5H9C5.96243 62.5 3.5 60.0376 3.5 57V43.5Z" fill="#E87503" stroke="black"/>
          {/* ... rest of the paths ... */}
        </g>
      </g>
    </svg>
  );