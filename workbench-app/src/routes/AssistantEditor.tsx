// Copyright (c) Microsoft. All rights reserved.

import { Card, Title3, Toolbar, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { AssistantConfiguration } from '../components/Assistants/AssistantConfiguration';
import { AssistantDelete } from '../components/Assistants/AssistantDelete';
import { AssistantDuplicate } from '../components/Assistants/AssistantDuplicate';
import { AssistantExport } from '../components/Assistants/AssistantExport';
import { AssistantRename } from '../components/Assistants/AssistantRename';
import { AssistantServiceMetadata } from '../components/Assistants/AssistantServiceMetadata';
import { MyConversations } from '../components/Conversations/MyConversations';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import {
    useAddConversationParticipantMutation,
    useCreateConversationMessageMutation,
    useGetAssistantConversationsQuery,
    useGetAssistantQuery,
} from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateRows: '1fr auto',
        height: '100%',
        gap: tokens.spacingVerticalM,
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
    content: {
        overflowY: 'auto',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    toolbar: {
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        borderRadius: tokens.borderRadiusMedium,
    },
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
});

export const AssistantEditor: React.FC = () => {
    const { assistantId } = useParams();
    if (!assistantId) {
        throw new Error('Assistant ID is required');
    }

    const classes = useClasses();
    const {
        data: assistantConversations,
        error: assistantConversationsError,
        isLoading: isLoadingAssistantConversations,
    } = useGetAssistantConversationsQuery(assistantId);
    const { data: assistant, error: assistantError, isLoading: isLoadingAssistant } = useGetAssistantQuery(assistantId);
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const localUserName = useAppSelector((state) => state.localUser.name);
    const siteUtility = useSiteUtility();
    const navigate = useNavigate();

    if (assistantConversationsError) {
        const errorMessage = JSON.stringify(assistantConversationsError);
        throw new Error(`Error loading assistant conversations: ${errorMessage}`);
    }

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isLoadingAssistant) return;
        if (!assistant) {
            throw new Error(`Assistant with ID ${assistantId} not found`);
        }
        siteUtility.setDocumentTitle(`Edit ${assistant.name}`);
    }, [assistantId, assistant, isLoadingAssistant, siteUtility]);

    const handleDelete = React.useCallback(() => {
        // navigate to site root
        siteUtility.forceNavigateTo('/');
    }, [siteUtility]);

    const handleDuplicate = (assistantId: string) => {
        siteUtility.forceNavigateTo(`/assistant/${assistantId}/edit`);
    };

    const handleConversationCreate = async (conversation: Conversation) => {
        // send event to notify the conversation that the user has joined
        await createConversationMessage({
            conversationId: conversation.id,
            content: `${localUserName ?? 'Unknown user'} created the conversation`,
            messageType: 'notice',
        });

        // send notice message first, to announce before assistant reacts to create event
        await createConversationMessage({
            conversationId: conversation.id,
            content: `${assistant?.name} added to conversation`,
            messageType: 'notice',
        });

        // add assistant to conversation
        await addConversationParticipant({ conversationId: conversation.id, participantId: assistantId });

        // navigate to conversation
        navigate(`/conversation/${conversation.id}`);
    };

    if (isLoadingAssistant || isLoadingAssistantConversations || !assistant) {
        return (
            <AppView title="Edit Assistant">
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView
            title={
                <div className={classes.title}>
                    <AssistantRename iconOnly assistant={assistant} />
                    <Title3>{assistant.name}</Title3>
                </div>
            }
        >
            <div className={classes.root}>
                <div className={classes.content}>
                    <Card className={classes.card}>
                        <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />
                    </Card>
                    <MyConversations
                        title="Conversations"
                        conversations={assistantConversations}
                        participantId={assistantId}
                        hideInstruction
                        onCreate={handleConversationCreate}
                    />
                    <Card className={classes.card}>
                        <AssistantConfiguration assistant={assistant} />
                    </Card>
                </div>
                <Toolbar className={classes.toolbar}>
                    <AssistantDelete asToolbarButton assistant={assistant} onDelete={handleDelete} />
                    <AssistantExport asToolbarButton assistantId={assistant.id} />
                    <AssistantDuplicate asToolbarButton assistant={assistant} onDuplicate={handleDuplicate} />
                </Toolbar>
            </div>
        </AppView>
    );
};
