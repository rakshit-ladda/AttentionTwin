import React from 'react';
import { 
  UserCheck, 
  BellRing, 
  GitCompare, 
  History, 
  AlertCircle, 
  Clock, 
  SlidersHorizontal 
} from 'lucide-react';
import { NavTab } from '../types';

interface PlaceholderSectionProps {
  tab: NavTab;
}

interface SectionMetadata {
  title: string;
  tagline: string;
  icon: React.ReactNode;
  targetPhase: string;
  cards: {
    title: string;
    description: string;
    points: string[];
    techSpec: {
      label: string;
      value: string;
    };
  }[];
}

const SECTION_DATA: Record<NavTab, SectionMetadata> = {
  profile: {
    title: 'Attention Profile',
    tagline: 'Cognitive state modeling, baseline responsiveness, and context sensitivity parameters',
    icon: <UserCheck size={28} />,
    targetPhase: 'Phase 2',
    cards: [
      {
        title: 'Cognitive State & Focus Baseline',
        description: 'Learns user responsiveness distributions across times of day and current task modes.',
        points: [
          'Temporal attention curve modeling (circadian alertness trends)',
          'Activity mode weighting (Deep Work, Meetings, Casual Browsing, Off-hours)',
          'Local SQLite persistence for personal profile parameters',
        ],
        techSpec: {
          label: 'Data Contract',
          value: 'ProfileParameters { focus_depth: float, interruption_cost: float, mode: str }',
        },
      },
      {
        title: 'Responsiveness Thresholds',
        description: 'Calibrates individual susceptibility to distraction without sending telemetry off-device.',
        points: [
          'Empirical response latency tracking from local interaction history',
          'Fatigue accumulation estimation during continuous work sessions',
          'Zero telemetry transmission: all profile weights reside in local storage',
        ],
        techSpec: {
          label: 'Storage Model',
          value: 'SQLite: attention_profiles table with versioned parameter snapshots',
        },
      },
    ],
  },
  simulator: {
    title: 'Notification Simulator',
    tagline: 'Interactive testing harness for incoming notifications and contextual variables',
    icon: <BellRing size={28} />,
    targetPhase: 'Phase 3',
    cards: [
      {
        title: 'Notification Event Synthesis',
        description: 'Allows structured input of incoming alerts to evaluate attention cost.',
        points: [
          'Configurable sender, application category, urgency, and content payload',
          'Contextual state attachment (current application, active focus timer, time of day)',
          'Validation schema enforced by Pydantic on backend API',
        ],
        techSpec: {
          label: 'API Endpoint Plan',
          value: 'POST /api/simulator/evaluate -> NotificationContext payload',
        },
      },
      {
        title: 'Action Space Definitions',
        description: 'Simulates the three core intervention policies for every incoming notification.',
        points: [
          'ALLOW: Immediate interruption delivered to user view',
          'SUPPRESS: Notification silenced and archived to digest',
          'DEFER: Notification scheduled for delivery during the next natural break window',
        ],
        techSpec: {
          label: 'Policy Matrix',
          value: 'InterventionAction = ["ALLOW", "SUPPRESS", "DEFER"]',
        },
      },
    ],
  },
  counterfactual: {
    title: 'Counterfactual Comparison',
    tagline: 'Side-by-side outcome estimation for identical notification context across ALLOW, SUPPRESS, and DEFER',
    icon: <GitCompare size={28} />,
    targetPhase: 'Phase 3 & 4',
    cards: [
      {
        title: 'The Counterfactual Engine',
        description: 'The defining core requirement: evaluating alternative realities for the exact same event.',
        points: [
          'Identical context: Same notification, same user cognitive state, same timing',
          'Triple-action evaluation: Predicted attention residue, task disruption, and information loss',
          'Local scikit-learn model estimates outcomes without external API dependencies',
        ],
        techSpec: {
          label: 'Engine Architecture',
          value: 'scikit-learn local regressors for DisruptionScore & UrgencyLoss',
        },
      },
      {
        title: 'Comparative Outcome Matrix',
        description: 'Multi-criteria trade-off view comparing outcomes under each candidate decision.',
        points: [
          'Immediate Distraction Cost (ALLOW vs SUPPRESS/DEFER)',
          'Information Delay Penalty (SUPPRESS vs ALLOW/DEFER)',
          'Net Attention Utility calculation to recommend optimal intervention',
        ],
        techSpec: {
          label: 'Decision Metric',
          value: 'Utility(Action) = -(DistractionCost) - (DelayPenalty) + (FocusGain)',
        },
      },
    ],
  },
  history: {
    title: 'History and Learning',
    tagline: 'Local feedback loop, model retraining records, and offline adaptation history',
    icon: <History size={28} />,
    targetPhase: 'Phase 4',
    cards: [
      {
        title: 'Interaction Log & Audit Trail',
        description: 'Tracks past notifications, chosen actions, and observed user responses.',
        points: [
          'Real notification response events recorded with timestamps and actions',
          'User feedback capture: Was this alert timely? Was the deferral helpful?',
          'No synthetic or pre-populated history displayed prior to actual recording',
        ],
        techSpec: {
          label: 'Schema Design',
          value: 'SQLite: interaction_logs (event_id, action_taken, outcome, feedback)',
        },
      },
      {
        title: 'Local Incremental Learning',
        description: 'Periodically refits local estimators as user feedback accumulates.',
        points: [
          'Offline retraining on accumulated local interaction logs',
          'Parameter drift detection to adapt to changing user schedules',
          'Zero cloud requirement: training runs completely on local CPU',
        ],
        techSpec: {
          label: 'Training Pipeline',
          value: 'Local scikit-learn pipeline retraining on SQLite interaction logs',
        },
      },
    ],
  },
};

export const PlaceholderSection: React.FC<PlaceholderSectionProps> = ({ tab }) => {
  const data = SECTION_DATA[tab];

  return (
    <div className="placeholder-container">
      <div className="section-hero">
        <div className="section-hero-header">
          <div className="section-title-wrap">
            <div className="section-icon-large">
              {data.icon}
            </div>
            <div>
              <h2 className="section-title">{data.title}</h2>
              <p className="section-tagline">{data.tagline}</p>
            </div>
          </div>
          <div className="unimplemented-badge">
            <Clock size={14} />
            <span>Not Yet Implemented ({data.targetPhase})</span>
          </div>
        </div>

        <div className="integrity-notice">
          <AlertCircle size={18} className="integrity-icon" />
          <div>
            <strong>Phase 1 Foundation Integrity:</strong> In accordance with strict engineering standards,
            no fabricated predictions, mock accuracy metrics, or artificial telemetry are displayed. 
            Real statistical inference and simulation models will be connected when their respective engines are implemented.
          </div>
        </div>
      </div>

      <div className="blueprint-grid">
        {data.cards.map((card, idx) => (
          <div key={idx} className="blueprint-card">
            <div className="card-header">
              <div className="card-title">
                <SlidersHorizontal size={16} />
                <span>{card.title}</span>
              </div>
              <span className="phase-pill">{data.targetPhase} Target</span>
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              {card.description}
            </p>

            <ul className="spec-list">
              {card.points.map((pt, pIdx) => (
                <li key={pIdx}>
                  <span className="spec-bullet">&bull;</span>
                  <span>{pt}</span>
                </li>
              ))}
            </ul>

            <div className="tech-spec-box">
              <div className="tech-spec-label">{card.techSpec.label}</div>
              <div>{card.techSpec.value}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
