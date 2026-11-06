
// import { useNavigate } from "react-router-dom";
// import {
//   Activity,
//   ArrowRight,
//   BarChart3,
//   BookOpen,
//   Clock3,
//   FileVideo,
//   History,
//   LayoutDashboard,
//   Mic2,
//   Target,
// } from "lucide-react";
// import "../dashboard.css";

// const team = [
//   "Kiran",
//   "Shrikanth Rao",
//   "Gagan Nagesh",
//   "Tharakhesh",
// ];

// export default function Dashboard() {
//   const navigate = useNavigate();

//   const navItems = [
//     { label: "Overview", icon: LayoutDashboard, path: "/dashboard" },
//     { label: "New Analysis", icon: FileVideo, path: "/upload" },
//     { label: "Detailed Final", icon: Target, path: "/detailed-final" },
//     { label: "Practice Speech", icon: Mic2, path: "/practice" },
//     { label: "History & Progress", icon: History, path: "/history" },
//   ];

//   return (
//     <div className="voxa-app">
//       <main className="voxa-main">
//         <header className="voxa-topbar">
//           <div>
//             <p className="eyebrow">YOUR PERSONAL SPEECH COACH</p>
//             <h2>Overview</h2>
//           </div>
//           <span className="status-label">
//             <span className="status-dot" /> AI COACH
//           </span>
//         </header>

//         <section className="welcome-panel">
//           <div className="welcome-content">
//             <span className="section-kicker">SPEAK WITH CONFIDENCE</span>
//             <h1>Your voice.<br />Your ideas. <span>Your impact.</span></h1>
//             <p>
//               VOXA is an AI-powered public speaking assistant that helps you
//               understand and improve the way you speak. Upload a presentation
//               recording to review your transcript, speaking pace, filler words,
//               pauses and pitch patterns, then use those insights to practise
//               with purpose.
//             </p>
//             <button
//               className="primary-button"
//               onClick={() => navigate("/upload")}
//             >
//               Start a new analysis <ArrowRight size={18} />
//             </button>
//           </div>

//           <div className="welcome-visual" aria-hidden="true">
//             <div className="visual-orbit orbit-one" />
//             <div className="visual-orbit orbit-two" />
//             <div className="visual-core"><Mic2 size={54} /></div>
//             <div className="visual-chip chip-top"><Activity size={17} /> Voice</div>
//             <div className="visual-chip chip-bottom"><BarChart3 size={17} /> Insights</div>
//           </div>
//         </section>

//         <section className="section-block">
//           <div className="section-heading">
//             <div>
//               <p className="eyebrow">HOW IT WORKS</p>
//               <h2>From recording to improvement</h2>
//             </div>
//           </div>

//           <div className="workflow-grid">
//             <article className="workflow-card">
//               <span className="step-number">01</span>
//               <FileVideo size={23} />
//               <h3>Upload</h3>
//               <p>Choose a recording of your speech or presentation.</p>
//             </article>
//             <article className="workflow-card">
//               <span className="step-number">02</span>
//               <Activity size={23} />
//               <h3>Analyse</h3>
//               <p>Extract speech metrics and a transcript from your recording.</p>
//             </article>
//             <article className="workflow-card">
//               <span className="step-number">03</span>
//               <BookOpen size={23} />
//               <h3>Improve</h3>
//               <p>Review the results and identify areas to practise.</p>
//             </article>
//           </div>
//         </section>

//         <section className="team-panel">
//           <div>
//             <p className="eyebrow">BUILT WITH PURPOSE</p>
//             <h2>Meet the builders</h2>
//             <p>
//               VOXA is a collaborative AI project focused on making public
//               speaking practice more measurable, accessible and actionable.
//             </p>
//           </div>
//           <div className="team-list">
//             {team.map((name, index) => (
//               <div className="team-member" key={name}>
//                 <span className="team-initial">{name.charAt(0)}</span>
//                 <span>{name}</span>
//                 <span className="team-index">0{index + 1}</span>
//               </div>
//             ))}
//           </div>
//         </section>

//         <footer className="voxa-footer">
//           <span>VOXA · AI PUBLIC SPEAKING COACH</span>
//           <span>Understand your voice. Improve your delivery.</span>
//         </footer>
//       </main>

//       <button
//         className="floating-analysis-button"
//         onClick={() => navigate("/upload")}
//       >
//         <Mic2 size={20} />
//         <span>Analyze My Speech</span>
//         <ArrowRight size={18} />
//       </button>
//     </div>
//   );
// }

import React from 'react';
import { ArrowRight, AudioLines, FileText, Clock3, Settings, ChartNoAxesColumn, Star, Video, Sparkles, TrendingUp, ShieldCheck } from 'lucide-react';
import '../dashboard.css';

const workflow = [
  { number: '01', title: 'Upload Video', desc: <>Add your recorded presentation<br />or speech video.</>, icon: Video, tone: 'green', to: '/upload' },
  { number: '02', title: 'Analyse', desc: <>Our AI processes your video<br />and extracts key metrics.</>, icon: Settings, tone: 'blue', to: '/upload' },
  { number: '03', title: 'View Insights', desc: <>Get detailed feedback on pace,<br />pitch, filler words and more.</>, icon: ChartNoAxesColumn, tone: 'blue', to: '/report' },
  { number: '04', title: 'Improve', desc: <>Practice, track progress<br />and become a better speaker.</>, icon: Star, tone: 'gold', to: '/practice' },
];
const builders = [
  { initial: 'K', name: 'Kiran', role: '-', color: 'sage' },
  { initial: 'S', name: 'Shrikanth Rao', role: '-', color: 'blue' },
  { initial: 'G', name: 'Gagan Nagesh', role: '-', color: 'teal' },
  { initial: 'T', name: 'Tharakhesh', role: '-', color: 'violet' },
];

function HeroOrb() {
  return <div className="sk-orb-stage" aria-label="Animated AI speech sphere">
    <div className="sk-orb-glow" />
    <svg className="sk-orb-svg" viewBox="0 0 560 390" role="img" aria-hidden="true">
      <defs>
        <radialGradient id="skOrbFill" cx="34%" cy="27%" r="78%"><stop offset="0" stopColor="#F7FFF5"/><stop offset=".23" stopColor="#9BE9C5"/><stop offset=".53" stopColor="#39B9C2"/><stop offset=".78" stopColor="#58BDEB"/><stop offset="1" stopColor="#C8F5EA"/></radialGradient>
        <radialGradient id="skOrbShine" cx="28%" cy="18%" r="75%"><stop offset="0" stopColor="#FFFFFF" stopOpacity=".95"/><stop offset=".32" stopColor="#E8FFF5" stopOpacity=".25"/><stop offset="1" stopColor="#D7FFFF" stopOpacity="0"/></radialGradient>
        <linearGradient id="skRing" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#B7F8C8"/><stop offset=".48" stopColor="#3BD4D8"/><stop offset="1" stopColor="#67C9F4"/></linearGradient>
        <filter id="skBlur"><feGaussianBlur stdDeviation="12"/></filter>
      </defs>
      <ellipse cx="278" cy="318" rx="125" ry="21" fill="#62D9E6" opacity=".23" filter="url(#skBlur)"/>
      <ellipse cx="278" cy="315" rx="105" ry="19" fill="none" stroke="#67D9E8" strokeWidth="7" opacity=".5"/>
      <ellipse cx="278" cy="311" rx="82" ry="12" fill="none" stroke="#B6F7DD" strokeWidth="5" opacity=".9"/>
      <circle cx="280" cy="172" r="119" fill="url(#skOrbFill)" stroke="#E7FFFA" strokeWidth="3"/>
      <circle cx="280" cy="172" r="119" fill="url(#skOrbShine)"/>
      <ellipse cx="247" cy="116" rx="66" ry="31" fill="#FFFFFF" opacity=".13" transform="rotate(-30 247 116)"/>
      <circle cx="280" cy="172" r="108" fill="none" stroke="#FFFFFF" strokeOpacity=".55" strokeWidth="1.4"/>
      <ellipse className="sk-orbit sk-orbit-a" cx="280" cy="173" rx="174" ry="47" fill="none" stroke="url(#skRing)" strokeWidth="5"/>
      <ellipse className="sk-orbit sk-orbit-b" cx="280" cy="173" rx="161" ry="58" fill="none" stroke="#8CEBE7" strokeWidth="2.5" opacity=".8"/>
      <ellipse className="sk-orbit sk-orbit-c" cx="280" cy="173" rx="151" ry="70" fill="none" stroke="#9BE8F8" strokeWidth="1.8" opacity=".7"/>
      <g fill="#EFFFFF" filter="url(#skBlur)" opacity=".85"><circle cx="280" cy="176" r="32"/></g>
      <g className="sk-wave" fill="#F4FFFF">
        <rect x="224" y="166" width="8" height="21" rx="4"/><rect x="239" y="148" width="8" height="57" rx="4"/><rect x="254" y="133" width="8" height="87" rx="4"/><rect x="269" y="112" width="8" height="117" rx="4"/><rect x="284" y="143" width="8" height="72" rx="4"/><rect x="299" y="158" width="8" height="41" rx="4"/><rect x="314" y="171" width="8" height="19" rx="4"/>
      </g>
      <circle cx="108" cy="104" r="12" fill="#72D8C3" stroke="#E8FFF8" strokeWidth="3"/><circle cx="435" cy="240" r="15" fill="#65D5C9" stroke="#E8FFF8" strokeWidth="3"/><circle cx="411" cy="64" r="6" fill="#78DCEB"/><circle cx="93" cy="270" r="7" fill="#75D9C9"/><circle cx="468" cy="97" r="5" fill="#8CE5E9"/>
      <path d="M35 165 C85 65 170 64 205 80 M362 71 C412 44 454 60 489 90 M65 216 C114 282 157 290 185 281" fill="none" stroke="#9CEBE4" strokeWidth="1.3" opacity=".5"/>
    </svg>
    <div className="sk-orb-note">Your voice<br />matters <span>↙</span></div>
  </div>;
}

export default function Dashboard() {
  const go = (path) => { window.location.href = path; };
  return (
    <main className="sk-dashboard">
      <section className="sk-hero">
        <div className="sk-hero-copy">
          <span className="sk-eyebrow">AI POWERED SPEECH COACH</span>
          <h1>
            Speak Better.
            <br />
            <span>Grow Faster.</span>
          </h1>
          <p>
            SpeakKaro.AI helps you analyse your speech, understand
            <br className="sk-desktop" /> your strengths, and improve with
            AI-powered insights.
          </p>
          <button className="sk-start-btn" onClick={() => go("/upload")}>
            <AudioLines size={21} /> Start Analysis <ArrowRight size={19} />
          </button>
          <div className="sk-benefits">
            <div>
              <span className="sk-benefit-icon">
                <FileText />
              </span>
              <span>
                <b>Transcripts</b>
                <small>Word by word</small>
              </span>
            </div>
            <i />
            <div>
              <span className="sk-benefit-icon">
                <Clock3 />
              </span>
              <span>
                <b>Real-time Metrics</b>
                <small>Pace, pitch, pauses</small>
              </span>
            </div>
            <i />
            <div>
              <span className="sk-benefit-icon">
                <Sparkles />
              </span>
              <span>
                <b>AI Insights</b>
                <small>Personalised feedback</small>
              </span>
            </div>
            <i />
            <div>
              <span className="sk-benefit-icon">
                <ShieldCheck />
              </span>
              <span>
                <b>Better You</b>
                <small>Confident speaker</small>
              </span>
            </div>
          </div>
        </div>
        <HeroOrb />
      </section>

      <section className="sk-workflow-section">
        <div className="sk-section-heading">
          <span className="sk-eyebrow">HOW IT WORKS</span>
          <h2>Your Workflow</h2>
          <p>From upload to insights — in just a few simple steps.</p>
        </div>
        <div className="sk-workflow-grid">
          {workflow.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.number}
                className={`sk-work-card ${item.tone}`}
                onClick={() => go(item.to)}
              >
                <div className="sk-work-card-top">
                  <span className="sk-step-number">{item.number}</span>
                  <span className="sk-work-icon">
                    <Icon size={25} />
                  </span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
                <ArrowRight className="sk-card-arrow" size={19} />
              </button>
            );
          })}
        </div>
      </section>

      <section className="sk-builders">
        <div className="sk-builders-intro">
          <span className="sk-eyebrow">BUILT WITH PASSION</span>
          <h2>Meet the Builders</h2>
          <p>
            A collaborative AI project focused on making public speaking
            practice more measurable, accessible and actionable.
          </p>
        </div>
        <div className="sk-builder-grid">
          {builders.map((person) => (
            <div className="sk-builder-card" key={person.name}>
              <span className={`sk-builder-avatar ${person.color}`}>
                {person.initial}
              </span>
              <b>{person.name}</b>
              <small>{person.role}</small>
            </div>
          ))}
        </div>
      </section>
      <footer className="sk-footer">
        <b>
          <AudioLines size={22} /> SpeakKaro<span>.AI</span>
        </b>
        <small>Speak. Analyse. Grow.</small>
        <div />
        <small>
          Built with care by Kiran, Shrikanth Rao, Gagan Nagesh &amp; Tharakhesh
        </small>
      </footer>
    </main>
  );
}
