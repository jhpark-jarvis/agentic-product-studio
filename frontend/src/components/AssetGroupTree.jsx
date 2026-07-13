import AddRoundedIcon from '@mui/icons-material/AddRounded'
import CreateRoundedIcon from '@mui/icons-material/CreateRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import FolderOpenRoundedIcon from '@mui/icons-material/FolderOpenRounded'
import FolderRoundedIcon from '@mui/icons-material/FolderRounded'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useState } from 'react'

function AssetGroupNode({
  node,
  depth,
  selectedPath,
  onSelect,
  onOpenCreate,
  onOpenRename,
  onOpenDelete,
  manageable,
}) {
  const isSelected = selectedPath === node.path

  return (
    <Stack spacing={1}>
      <Stack
        direction="row"
        spacing={1}
        sx={{
          alignItems: 'center',
          pl: depth * 2,
          pr: 1,
          py: 0.5,
          borderRadius: 2,
          bgcolor: isSelected ? 'action.selected' : 'transparent',
        }}
      >
        <Button
          variant={isSelected ? 'contained' : 'text'}
          color={isSelected ? 'primary' : 'inherit'}
          startIcon={isSelected ? <FolderOpenRoundedIcon /> : <FolderRoundedIcon />}
          onClick={() => onSelect(node.path)}
          sx={{
            minWidth: 0,
            px: 1,
            justifyContent: 'flex-start',
            textAlign: 'left',
            flexGrow: 1,
          }}
        >
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: isSelected ? 700 : 500,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {node.name}
            </Typography>
            <Chip size="small" variant="outlined" label={node.total_asset_count} />
          </Stack>
        </Button>

        {manageable ? (
          <Stack direction="row" spacing={0.25}>
            <IconButton size="small" onClick={() => onOpenCreate(node.path)} title="하위 폴더 추가">
              <AddRoundedIcon fontSize="inherit" />
            </IconButton>
            <IconButton size="small" onClick={() => onOpenRename(node)} title="이름 변경">
              <CreateRoundedIcon fontSize="inherit" />
            </IconButton>
            <IconButton size="small" onClick={() => onOpenDelete(node)} title="삭제">
              <DeleteOutlineRoundedIcon fontSize="inherit" />
            </IconButton>
          </Stack>
        ) : null}
      </Stack>

      {node.children?.length
        ? node.children.map((child) => (
            <AssetGroupNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
              onOpenCreate={onOpenCreate}
              onOpenRename={onOpenRename}
              onOpenDelete={onOpenDelete}
              manageable={manageable}
            />
          ))
        : null}
    </Stack>
  )
}

export function AssetGroupTree({
  tree = [],
  selectedPath = '',
  ungroupedCount = 0,
  ungroupedSelectValue = '',
  ungroupedLabel = '그룹 미지정',
  manageable = false,
  busy = false,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}) {
  const [dialogMode, setDialogMode] = useState('')
  const [activeNode, setActiveNode] = useState(null)
  const [parentPath, setParentPath] = useState('')
  const [folderName, setFolderName] = useState('')

  const closeDialog = () => {
    if (busy) {
      return
    }
    setDialogMode('')
    setActiveNode(null)
    setParentPath('')
    setFolderName('')
  }

  const openCreate = (nextParentPath = '') => {
    setDialogMode('create')
    setParentPath(nextParentPath)
    setActiveNode(null)
    setFolderName('')
  }

  const openRename = (node) => {
    setDialogMode('rename')
    setActiveNode(node)
    setParentPath('')
    setFolderName(node?.name || '')
  }

  const openDelete = (node) => {
    setDialogMode('delete')
    setActiveNode(node)
    setParentPath('')
    setFolderName('')
  }

  const handleConfirm = async () => {
    try {
      if (dialogMode === 'create') {
        await onCreate?.({ parentPath, name: folderName.trim() })
        closeDialog()
        return
      }
      if (dialogMode === 'rename') {
        await onRename?.({ path: activeNode?.path || '', newName: folderName.trim() })
        closeDialog()
        return
      }
      if (dialogMode === 'delete') {
        await onDelete?.({ path: activeNode?.path || '' })
        closeDialog()
      }
    } catch (_error) {
      // The parent page already surfaces the API error.
    }
  }

  return (
    <Stack spacing={1.5}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
        <Button
          variant={selectedPath === ungroupedSelectValue ? 'contained' : 'outlined'}
          onClick={() => onSelect?.(ungroupedSelectValue)}
          startIcon={<FolderOpenRoundedIcon />}
        >
          {ungroupedLabel}
        </Button>
        <Chip size="small" variant="outlined" label={`미지정 ${ungroupedCount}`} sx={{ alignSelf: 'center' }} />
        {manageable ? (
          <Button variant="outlined" startIcon={<AddRoundedIcon />} onClick={() => openCreate('')}>
            루트 폴더 추가
          </Button>
        ) : null}
      </Stack>

      {tree.length ? (
        <Stack spacing={0.75}>
          {tree.map((node) => (
            <AssetGroupNode
              key={node.path}
              node={node}
              depth={0}
              selectedPath={selectedPath}
              onSelect={onSelect}
              onOpenCreate={openCreate}
              onOpenRename={openRename}
              onOpenDelete={openDelete}
              manageable={manageable}
            />
          ))}
        </Stack>
      ) : (
        <Box
          sx={{
            px: 2,
            py: 3,
            border: '1px dashed',
            borderColor: 'divider',
            borderRadius: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            아직 등록된 폴더가 없습니다.
          </Typography>
        </Box>
      )}

      <Dialog open={Boolean(dialogMode)} onClose={closeDialog} fullWidth maxWidth="xs">
        <DialogTitle>
          {dialogMode === 'create'
            ? '폴더 추가'
            : dialogMode === 'rename'
              ? '폴더 이름 변경'
              : '폴더 삭제'}
        </DialogTitle>
        <DialogContent>
          {dialogMode === 'delete' ? (
            <Typography variant="body2" color="text.secondary" sx={{ pt: 1 }}>
              `{activeNode?.path}` 폴더를 삭제합니다. 하위 Asset이 남아 있으면 삭제되지 않습니다.
            </Typography>
          ) : (
            <Stack spacing={1.5} sx={{ pt: 1 }}>
              {dialogMode === 'create' && parentPath ? (
                <Typography variant="body2" color="text.secondary">
                  상위 경로: {parentPath}
                </Typography>
              ) : null}
              <TextField
                autoFocus
                label="폴더 이름"
                value={folderName}
                onChange={(event) => setFolderName(event.target.value)}
                placeholder="예: ui, towns, npc"
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={busy}>
            취소
          </Button>
          <Button
            onClick={handleConfirm}
            variant="contained"
            color={dialogMode === 'delete' ? 'error' : 'primary'}
            disabled={busy || ((dialogMode === 'create' || dialogMode === 'rename') && !folderName.trim())}
          >
            {dialogMode === 'delete' ? '삭제' : '확인'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}
