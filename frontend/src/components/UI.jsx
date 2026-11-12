// Small shared presentation components with consistent empty, loading and error treatment.
import React from 'react';
import { ArrowUpRight, LoaderCircle } from 'lucide-react';
/** Render a semantic action with an optional icon and visible pending state. */
export function Button({children,onClick,secondary=false,disabled=false,busy=false,className='',...props}) {return <button className={`button ${secondary?'secondary':''} ${className}`} onClick={onClick} disabled={disabled||busy} {...props}>{busy&&<LoaderCircle size={16} className="spin"/>}{children}</button>;}
/** Render a page introduction with a small research-style section index. */
export function PageHead({eyebrow,title,description,action}) {return <header className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description&&<p>{description}</p>}</div>{action}</header>;}
/** Format elapsed session time consistently in game and history panels. */
export function clock(seconds) {return `${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')}`;}
/** Format actual metrics, preserving zero rather than displaying an empty value. */
export function Metric({label,value,unit}) {return <div className="metric"><span>{label}</span><strong>{value??'—'}<small>{unit}</small></strong></div>;}
/** Show nonblocking errors and status updates to assistive technology. */
export function Notice({children,error=false}) {return children?<div className={`notice ${error?'error':''}`} role={error?'alert':'status'}>{children}</div>:null;}
/** Reject a failed integrity report visibly instead of presenting only its valid proof prefix. */
export function ProofStatus({report}) {if(!report)return null;return report.valid===false?<Notice error>Trace integrity verification failed at steps {report.failures.join(', ')}.</Notice>:<div className="proof-banner">✓ {report.verified}/{report.total} deduction and forced-assignment steps formally verified · {report.assumptions} explicit assumptions</div>;}
