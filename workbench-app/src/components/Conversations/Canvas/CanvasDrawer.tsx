import { makeStyles, mergeClasses, shorthands, Title3, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    drawerContainer: {
        top: 0,
        height: '100%',
        transition: `width ${tokens.durationNormal} ${tokens.curveEasyEase}`,
        overflow: 'auto',
        backgroundColor: tokens.colorNeutralBackground1,
        zIndex: tokens.zIndexOverlay,
        boxShadow: tokens.shadow8Brand,
    },
    drawerTitle: {
        ...shorthands.padding(
            tokens.spacingVerticalXXL,
            tokens.spacingHorizontalXXL,
            tokens.spacingVerticalS,
            tokens.spacingHorizontalXXL,
        ),
    },
    drawerContent: {
        padding: tokens.spacingHorizontalM,
        overflow: 'auto',
    },
});

interface CanvasDrawerProps {
    openClassName?: string;
    className?: string;
    open?: boolean;
    mode?: 'inline' | 'overlay';
    side?: 'left' | 'right';
    title?: string | React.ReactNode;
    children?: React.ReactNode;
}

export const CanvasDrawer: React.FC<CanvasDrawerProps> = (props) => {
    const { openClassName, className, open, mode, side, title, children } = props;
    const classes = useClasses();

    const drawerStyle: React.CSSProperties = {
        right: side === 'right' ? 0 : undefined,
        width: open ? undefined : '0px',
        position: mode === 'inline' ? 'relative' : 'fixed',
    };

    const titleContent = typeof title === 'string' ? <Title3>{title}</Title3> : title;

    return (
        <div
            style={drawerStyle}
            className={mergeClasses(className, open ? openClassName : '', classes.drawerContainer)}
        >
            <div className={classes.drawerTitle}>{titleContent}</div>
            <div className={classes.drawerContent}>{children}</div>
        </div>
    );
};
