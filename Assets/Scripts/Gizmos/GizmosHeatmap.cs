using UnityEngine;
using System.Collections.Generic;
using RobotSimulation.Controllers;

namespace RobotSimulation.Gizmos
{
    /// <summary>
    /// Visualizes a heatmap of robot joint positions over time using Gizmos.
    /// Hot zones (red) indicate frequently visited areas, cold zones (blue) indicate rarely visited areas.
    /// </summary>
    public class GizmosHeatmap : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private RobotController _robotController;

        [Header("Grid Configuration")]
        [Tooltip("Size of each cell in the heatmap grid (meters)")]
        [SerializeField] private float _cellSize = 0.05f;

        [Tooltip("Maximum heat value for color normalization")]
        [SerializeField] private int _maxHeatValue = 100;

        [Header("Visualization")]
        [Tooltip("Transparency of the heatmap gizmos")]
        [Range(0.1f, 1.0f)]
        [SerializeField] private float _gizmoAlpha = 0.6f;

        [Tooltip("Size multiplier for the drawn cubes")]
        [Range(0.1f, 2.0f)]
        [SerializeField] private float _cubeScale = 0.8f;

        [Header("Performance")]
        [Tooltip("How often to sample positions (1 = every FixedUpdate, 2 = every other, etc.)")]
        [SerializeField] private int _sampleInterval = 1;

        private Dictionary<Vector3Int, int> _heatmapGrid;
        private int _frameCounter;
        private bool _isInitialized;

        /// <summary>
        /// Initialize the heatmap with a reference to the RobotController.
        /// Called by GameManager during centralized initialization.
        /// </summary>
        public void Initialize(RobotController robotController)
        {
            _robotController = robotController;
            InitializeInternal();
        }

        /// <summary>
        /// Clears all accumulated heatmap data.
        /// </summary>
        public void ClearHeatmap()
        {
            if (_heatmapGrid != null)
            {
                _heatmapGrid.Clear();
            }
            Debug.Log("GizmosHeatmap: Heatmap data cleared.");
        }

        /// <summary>
        /// Returns the total number of recorded positions.
        /// </summary>
        public int GetTotalSamples()
        {
            if (_heatmapGrid == null)
            {
                return 0;
            }

            int total = 0;
            foreach (KeyValuePair<Vector3Int, int> entry in _heatmapGrid)
            {
                total += entry.Value;
            }
            return total;
        }

        /// <summary>
        /// Returns the number of unique cells in the grid.
        /// </summary>
        public int GetUniqueCellCount()
        {
            return _heatmapGrid != null ? _heatmapGrid.Count : 0;
        }

        private void Awake()
        {
            InitializeInternal();
        }

        private void InitializeInternal()
        {
            if (_isInitialized)
            {
                return;
            }

            _heatmapGrid = new Dictionary<Vector3Int, int>();
            _frameCounter = 0;
            _isInitialized = true;
        }

        private void FixedUpdate()
        {
            if (_robotController == null)
            {
                return;
            }

            _frameCounter++;

            if (_frameCounter % _sampleInterval != 0)
            {
                return;
            }

            SampleColliderPositions();
        }

        private void SampleColliderPositions()
        {
            Collider[] colliders = _robotController.GetAllJointColliders();

            foreach (Collider collider in colliders)
            {
                if (collider == null)
                {
                    continue;
                }

                Vector3 worldPosition = collider.bounds.center;
                Vector3Int gridPosition = WorldToGridPosition(worldPosition);

                if (_heatmapGrid.ContainsKey(gridPosition))
                {
                    _heatmapGrid[gridPosition]++;
                }
                else
                {
                    _heatmapGrid[gridPosition] = 1;
                }
            }
        }

        private Vector3Int WorldToGridPosition(Vector3 worldPosition)
        {
            int gridX = Mathf.FloorToInt(worldPosition.x / _cellSize);
            int gridY = Mathf.FloorToInt(worldPosition.y / _cellSize);
            int gridZ = Mathf.FloorToInt(worldPosition.z / _cellSize);

            return new Vector3Int(gridX, gridY, gridZ);
        }

        private Vector3 GridToWorldPosition(Vector3Int gridPosition)
        {
            float worldX = (gridPosition.x + 0.5f) * _cellSize;
            float worldY = (gridPosition.y + 0.5f) * _cellSize;
            float worldZ = (gridPosition.z + 0.5f) * _cellSize;

            return new Vector3(worldX, worldY, worldZ);
        }

        private Color GetHeatColor(int heatValue)
        {
            // Normalize heat value between 0 and 1
            float normalizedHeat = Mathf.Clamp01((float)heatValue / _maxHeatValue);

            // Color gradient: Blue (cold) -> Cyan -> Green -> Yellow -> Red (hot)
            Color resultColor;

            if (normalizedHeat < 0.25f)
            {
                // Blue to Cyan
                float t = normalizedHeat / 0.25f;
                resultColor = Color.Lerp(Color.blue, Color.cyan, t);
            }
            else if (normalizedHeat < 0.5f)
            {
                // Cyan to Green
                float t = (normalizedHeat - 0.25f) / 0.25f;
                resultColor = Color.Lerp(Color.cyan, Color.green, t);
            }
            else if (normalizedHeat < 0.75f)
            {
                // Green to Yellow
                float t = (normalizedHeat - 0.5f) / 0.25f;
                resultColor = Color.Lerp(Color.green, Color.yellow, t);
            }
            else
            {
                // Yellow to Red
                float t = (normalizedHeat - 0.75f) / 0.25f;
                resultColor = Color.Lerp(Color.yellow, Color.red, t);
            }

            resultColor.a = _gizmoAlpha;
            return resultColor;
        }

        private void OnDrawGizmos()
        {
            if (_heatmapGrid == null || _heatmapGrid.Count == 0)
            {
                return;
            }

            Vector3 cubeSize = new Vector3(_cellSize * _cubeScale, _cellSize * _cubeScale, _cellSize * _cubeScale);

            foreach (KeyValuePair<Vector3Int, int> entry in _heatmapGrid)
            {
                Vector3Int gridPosition = entry.Key;
                int heatValue = entry.Value;

                Vector3 worldPosition = GridToWorldPosition(gridPosition);
                Color gizmoColor = GetHeatColor(heatValue);

                UnityEngine.Gizmos.color = gizmoColor;
                UnityEngine.Gizmos.DrawCube(worldPosition, cubeSize);
            }
        }
    }
}
