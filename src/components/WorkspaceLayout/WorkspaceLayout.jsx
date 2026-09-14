import React from 'react';
import styles from './WorkspaceLayout.module.css';

export function WorkspaceLayout({ leftPanel, centerPanel, rightPanel }) {
  return (
    <div className={styles.layout}>
      <div className={styles.leftPanel}>
        {leftPanel}
      </div>
      <div className={styles.centerPanel}>
        {centerPanel}
      </div>
      <div className={styles.rightPanel}>
        {rightPanel}
      </div>
    </div>
  );
}
