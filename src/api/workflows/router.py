from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from .schemas import CreateWorkflowRequest, WorkflowExecuteRequest
from .service import (
    list_workflows,
    create_workflow,
    get_workflow,
    delete_workflow,
    execute_workflow
)

# Create router for user workflows
router = APIRouter(
    prefix="/users/{user_id}/workflows",
    tags=["workflows"]
)


@router.get("")
async def list_workflows_endpoint(
        user_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    List all workflows for a user.
    
    Args:
        user_id: UUID of the user
        session: Database session dependency
            
    Returns:
        List of workflows with their nodes and connections
    """
    return await list_workflows(session)


@router.post("", status_code=201)
async def create_workflow_endpoint(
        user_id: UUID,
        request: CreateWorkflowRequest,
        session: AsyncSession = Depends(get_session)
):
    """
    Create a new workflow for a user.
    
    Args:
        user_id: UUID of the user
        request: The workflow creation request
        session: Database session dependency
            
    Returns:
        The created workflow instance with its ID
    """
    workflow_id = uuid4()
    workflow = await create_workflow(workflow_id, request, session)
    return workflow


@router.get("/{workflow_id}")
async def get_workflow_endpoint(
        user_id: UUID,
        workflow_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    Get a workflow by its ID.
    
    Args:
        user_id: UUID of the user
        workflow_id: UUID of the workflow to retrieve
        session: Database session dependency
        
    Returns:
        The workflow if found
    """
    return await get_workflow(workflow_id, session)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow_endpoint(
        user_id: UUID,
        workflow_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    Delete a workflow by its ID.
    
    Args:
        user_id: UUID of the user
        workflow_id: UUID of the workflow to delete
        session: Database session dependency
        
    Returns:
        No content on success
    """
    await delete_workflow(workflow_id, session)
    return None


@router.post("/{workflow_id}/execute")
async def execute_workflow_endpoint(
        user_id: UUID,
        workflow_id: UUID,
        request: WorkflowExecuteRequest,
        session: AsyncSession = Depends(get_session)
):
    """
    Execute a workflow with the given input values.
    
    Args:
        user_id: UUID of the user
        workflow_id: UUID of the workflow to execute
        request: The workflow execution request
        session: Database session dependency
            
    Returns:
        The outputs from all leaf nodes
    """
    return await execute_workflow(workflow_id, request, session) 