// Copyright (c) Microsoft. All rights reserved.

import {
    SelectTabData,
    SelectTabEvent,
    SelectTabEventHandler,
    Tab,
    TabList,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { AssistantStateDescription } from '../../../models/AssistantStateDescription';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantInspector } from './AssistantInspector';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: 'auto 1fr',
        height: '100%',
    },
    header: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    headerContent: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    body: {
        overflowY: 'auto',
        height: '100%',
        maxHeight: '100%',
    },
});

interface AssistantInspectorListProps {
    conversationId: string;
    stateDescriptions: AssistantStateDescription[];
}

export const AssistantInspectorList: React.FC<AssistantInspectorListProps> = (props) => {
    const { conversationId, stateDescriptions } = props;
    const classes = useClasses();
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const interactCanvasController = useInteractCanvasController();

    const onTabSelect: SelectTabEventHandler = (_event: SelectTabEvent, data: SelectTabData) => {
        interactCanvasController.transitionToState({ assistantStateId: data.value as string });
    };

    const selectedTab = interactCanvasState?.assistantStateId ?? stateDescriptions[0].id;
    const selectedStateDescription = stateDescriptions.find((stateDescription) => stateDescription.id === selectedTab);

    if (!interactCanvasState?.assistantId) return null;

    if (stateDescriptions.length === 0) {
        return (
            <div className={classes.root}>
                <div className={classes.header}>
                    <div className={classes.headerContent}>
                        <div>No assistant state inspectors available</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <div className={classes.headerContent}>
                    <TabList selectedValue={selectedTab} onTabSelect={onTabSelect} size="small">
                        {stateDescriptions
                            .filter((stateDescription) => stateDescription.id !== 'config')
                            .map((stateDescription) => (
                                <Tab key={stateDescription.id} value={stateDescription.id}>
                                    {stateDescription.displayName}
                                </Tab>
                            ))}
                    </TabList>
                </div>
            </div>
            {selectedStateDescription && (
                <div className={classes.body}>
                    <AssistantInspector
                        assistantId={interactCanvasState?.assistantId}
                        conversationId={conversationId}
                        stateDescription={selectedStateDescription}
                    />
                </div>
            )}
        </div>
    );
};
