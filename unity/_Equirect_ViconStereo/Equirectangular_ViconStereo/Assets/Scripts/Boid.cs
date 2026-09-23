//using System.Collections;
//using System.Collections.Generic;
using UnityEngine;

public class Boid : MonoBehaviour
{
    [HideInInspector] public Vector3 Velocity;

    // デバッグ（洗濯時に進行方向の線を描画）
    public Color GizmoColor = Color.cyan;

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = GizmoColor;
        Vector3 p = transform.position;
        Vector3 d = (Velocity.sqrMagnitude > 1e-6f) ? Velocity.normalized: transform.forward;
        Gizmos.DrawLine(p, p+d*0.6f);
    }

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}

